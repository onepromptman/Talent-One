#!/usr/bin/env python3
"""ats_fetch.py - Greenhouse Harvest -> Talent One KB writer.

Responsibility (see ATS_FETCH_CONTRACT.md, the authoritative spec): fill the ATS
T0 slot with *aggregate, PII-free* house signal, written as provenance-pilled
Markdown into the operator's KB root so the runner's kb_search (Read/Grep over an
--add-dir'd directory) finds it with no agent-prompt change. The tool writes KB
files only; it changes no agent and no template.

Zero third-party dependencies (urllib + stdlib) on purpose, to preserve the
runner's "no pip installs" property. Auth: HTTP Basic, username = the Harvest API
key, empty password; the key is read from the environment only (never a flag,
never committed) and masked (last 4) anywhere it is logged.

Hard PII rule (contract sec 5): no candidate name/email/phone or any candidate
object field is ever read into or written out of this tool. Offers become counts
+ de-identified comp statistics; applications become per-stage counts. A comp
level is emitted only at or above MIN_COMP_N offers so a single offer cannot be
re-identified. Where Greenhouse is silent, the tool writes NOTHING (no zero-fill)
so agents fall back to the supported Estimate/Oracle path.

Precedence note (contract sec 3): offers-<rf>.md holds ATS accepted-offer
actuals, which sit BELOW a comp-system approved band in grounding-matrix Part 2.
It is deliberately never written to internal/comp/bands.csv (reserved for the
comp-system band export) so the precedence rule stays legible.

Fixture filename scheme (--fixture <dir>) - one JSON file per Harvest collection,
each a JSON list of records shaped as Harvest returns them:

    jobs.json          GET /v1/jobs           (id, name/title, departments[], opened_at, closed_at)
    job_posts.json     GET /v1/job_posts      (job_id, title, content)
    offers.json        GET /v1/offers         (job_id, status, level, salary, ...)
    applications.json  GET /v1/applications   (job_id(s), current_stage.name, status)
    scorecards.json    GET /v1/scorecards     (job_id, attributes[]/questions[])  [optional]

Design choices (documented deviations from a naive per-job crawl):
- Funnel is derived by aggregating application current_stage across a role family,
  bucketed into the canonical Application->Screen->Onsite->Offer->Hire order. This
  avoids an N+1 /v1/jobs/{id}/stages call per job.
- Interview structure is derived from scorecards.json attribute names only; if the
  file is absent, no interview file is written.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime
import fnmatch
import json
import os
import statistics
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import runlog

log = runlog.get_logger("talent-one.ats_fetch")

HARVEST_BASE = "https://harvest.greenhouse.io"
ENV_KEY = "GREENHOUSE_HARVEST_KEY"
PER_PAGE = 500
MAX_RETRIES = 5  # for 429 / transient 5xx only; other 4xx never retried
MIN_COMP_N = 3  # do not emit a comp level below this many offers (re-id guard)

# Canonical funnel buckets, in order. A stage name is bucketed by the first keyword
# it contains (case-insensitive); anything unmatched lands in "Other" (counted, but
# reported separately from the named stage buckets).
STAGE_BUCKETS = [
    ("Application", ("application", "applied", "new", "sourced", "prospect")),
    ("Screen", ("screen", "phone", "recruiter")),
    (
        "Onsite",
        ("onsite", "interview", "assessment", "technical", "take-home", "take home"),
    ),
    ("Offer", ("offer",)),
    ("Hire", ("hire", "hired")),
]

# Candidate-object keys the tool must never read or emit. Enforced by construction
# (the aggregation functions below never touch them) and asserted by the test suite.
PII_KEYS = (
    "name",
    "first_name",
    "last_name",
    "email",
    "email_addresses",
    "phone",
    "phone_numbers",
    "candidate",
    "candidate_id",
)


# ------------------------------------------------------------------------- helpers
def die(msg: str, code: int = 1):
    print(f"ERROR  {msg}", file=sys.stderr)
    sys.exit(code)


def mask(secret: str) -> str:
    return f"****{secret[-4:]}" if secret and len(secret) >= 4 else "****"


def today() -> str:
    return datetime.date.today().isoformat()


def pill() -> str:
    return f"Sourced · Greenhouse {today()}"


def _job_ids_of(rec: dict) -> list:
    """Robustly extract the job id(s) a record (application/offer/post/scorecard)
    belongs to, across the shapes Harvest uses."""
    ids = []
    if rec.get("job_id") is not None:
        ids.append(rec["job_id"])
    for j in rec.get("jobs", []) or []:
        if isinstance(j, dict) and j.get("id") is not None:
            ids.append(j["id"])
        elif isinstance(j, (int, str)):
            ids.append(j)
    ids.extend(rec.get("job_ids", []) or [])
    return ids


# ------------------------------------------------------------------------- sources
class LiveSource:
    """Reads Harvest collections over HTTPS with Basic auth and pagination."""

    def __init__(self, key: str, base: str = HARVEST_BASE):
        token = base64.b64encode(f"{key}:".encode()).decode()
        self._auth = f"Basic {token}"
        self._key = key
        self._base = base

    def collection(self, name: str) -> list:
        out, page = [], 1
        while True:
            url = f"{self._base}/v1/{name}?per_page={PER_PAGE}&page={page}"
            batch = self._get(url)
            if not isinstance(batch, list):
                die(f"unexpected Harvest response for {name}: not a list")
            out.extend(batch)
            if len(batch) < PER_PAGE:
                return out
            page += 1

    def _get(self, url: str):
        for attempt in range(MAX_RETRIES + 1):
            req = urllib.request.Request(url, headers={"Authorization": self._auth})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429 or 500 <= e.code < 600:
                    if attempt < MAX_RETRIES:
                        log.warning(
                            "Harvest %s, retry %d of %d in %ds",
                            e.code,
                            attempt + 1,
                            MAX_RETRIES,
                            2**attempt,
                        )
                        time.sleep(2**attempt)  # exponential backoff
                        continue
                    die(
                        f"Harvest {e.code} after {MAX_RETRIES} retries "
                        f"(key {mask(self._key)}): {url}"
                    )
                # any other 4xx: never retry
                die(f"Harvest {e.code} (key {mask(self._key)}): {url}")
            except urllib.error.URLError as e:
                if attempt < MAX_RETRIES:
                    log.warning(
                        "Harvest network error (%s), retry %d of %d in %ds",
                        e.reason,
                        attempt + 1,
                        MAX_RETRIES,
                        2**attempt,
                    )
                    time.sleep(2**attempt)
                    continue
                die(f"Harvest network error after {MAX_RETRIES} retries: {e.reason}")


class FixtureSource:
    """Reads canned Harvest collections from <dir>/<name>.json for offline runs."""

    def __init__(self, root: Path):
        self._root = Path(root)

    def collection(self, name: str) -> list:
        f = self._root / f"{name}.json"
        if not f.exists():
            return []
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []


# --------------------------------------------------------------------- role family
def load_crosswalk(path: Path) -> list:
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rf = (row.get("role_family") or "").strip()
            if not rf or rf.startswith("#"):
                continue
            rows.append(
                {
                    "role_family": rf,
                    "gh_department": (row.get("gh_department") or "").strip(),
                    "gh_title_match": (row.get("gh_title_match") or "").strip(),
                }
            )
    return rows


def _job_departments(job: dict) -> list:
    names = []
    for d in job.get("departments", []) or []:
        if isinstance(d, dict) and d.get("name"):
            names.append(d["name"])
    if job.get("department"):
        names.append(job["department"])
    return names


def match_family(job: dict, rows: list) -> str | None:
    """Return the first role_family whose department or title rule matches this job."""
    title = (job.get("name") or job.get("title") or "").lower()
    depts = [d.lower() for d in _job_departments(job)]
    for row in rows:
        dep = row["gh_department"].lower()
        if dep and any(dep in d for d in depts):
            return row["role_family"]
        patterns = [
            p.strip().lower() for p in row["gh_title_match"].split("|") if p.strip()
        ]
        if any(fnmatch.fnmatch(title, p) for p in patterns):
            return row["role_family"]
    return None


def bucket_stage(name: str) -> str:
    low = (name or "").lower()
    for bucket, keys in STAGE_BUCKETS:
        if any(k in low for k in keys):
            return bucket
    return "Other"


# ------------------------------------------------------------------- aggregations
def build_funnel(apps: list) -> dict | None:
    """Aggregate current stage counts from the applications snapshot."""
    if not apps:
        return None
    counts = {}
    for a in apps:
        stage = bucket_stage(
            (a.get("current_stage") or {}).get("name")
            if isinstance(a.get("current_stage"), dict)
            else a.get("current_stage")
        )
        counts[stage] = counts.get(stage, 0) + 1
    ordered = [(b, counts[b]) for b, _ in STAGE_BUCKETS if b in counts]
    if not ordered:
        return None
    other = counts.get("Other")
    return {
        "stages": ordered,
        "other": other,
        "total": sum(counts.values()),
    }


def _salary_of(offer: dict):
    s = offer.get("salary")
    if isinstance(s, (int, float)):
        return float(s)
    ss = offer.get("starting_salary")
    if isinstance(ss, dict) and isinstance(ss.get("value"), (int, float)):
        return float(ss["value"])
    if isinstance(ss, (int, float)):
        return float(ss)
    return None


def build_offers(offers: list) -> dict | None:
    """De-identified accepted-offer comp stats by level. A level is emitted only at
    or above MIN_COMP_N offers (re-identification guard)."""
    by_level = {}
    for o in offers:
        if str(o.get("status", "accepted")).lower() not in ("accepted", "signed", ""):
            continue
        sal = _salary_of(o)
        if sal is None:
            continue
        lvl = str(o.get("level") or "unspecified")
        by_level.setdefault(lvl, []).append(sal)
    rows = []
    for lvl, sals in sorted(by_level.items()):
        if len(sals) < MIN_COMP_N:
            continue  # silence rather than risk re-identification
        rows.append(
            {
                "level": lvl,
                "n": len(sals),
                "min": min(sals),
                "median": statistics.median(sals),
                "max": max(sals),
            }
        )
    return {"levels": rows} if rows else None


def build_tth(jobs: list) -> dict | None:
    days = []
    for j in jobs:
        o, c = j.get("opened_at"), j.get("closed_at")
        if not o or not c:
            continue
        try:
            do = datetime.date.fromisoformat(o[:10])
            dc = datetime.date.fromisoformat(c[:10])
        except ValueError:
            continue
        days.append((dc - do).days)
    if not days:
        return None
    return {
        "n": len(days),
        "median_days": round(statistics.median(days)),
        "min_days": min(days),
        "max_days": max(days),
    }


def build_postings(posts: list) -> dict | None:
    items = []
    for p in posts[:5]:
        content = (p.get("content") or "").strip()
        if not content:
            continue
        items.append(
            {
                "title": (p.get("title") or "").strip(),
                "updated_at": (p.get("updated_at") or "")[:10],
                "content": content,
            }
        )
    return {"posts": items} if items else None


def build_interview(scorecards: list) -> dict | None:
    attrs = []
    seen = set()
    for sc in scorecards:
        for a in sc.get("attributes", []) or sc.get("questions", []) or []:
            label = a.get("name") if isinstance(a, dict) else str(a)
            if label and label not in seen:
                seen.add(label)
                attrs.append(label)
    return {"attributes": attrs} if attrs else None


# ------------------------------------------------------------------------- writers
def _atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _header(rf: str, kind: str, n_note: str = "") -> str:
    line = f"# {kind} · {rf}\n\n> {pill()} · role_family: `{rf}`"
    if n_note:
        line += f" · {n_note}"
    return line + "\n\n"


def write_funnel(out: Path, rf: str, f: dict) -> Path:
    body = [_header(rf, "Current stage counts", f"total applications n={f['total']}")]
    body.append(
        "Each application counts once at its current stage. Use cumulative "
        "counts for one cohort to calculate conversion rates.\n\n"
    )
    body.append("| Stage | n |\n|---|---|\n")
    for stage, n in f["stages"]:
        body.append(f"| {stage} | {n} |\n")
    if f.get("other"):
        body.append(f"| Other (unbucketed) | {f['other']} |\n")
    dest = out / "internal" / "funnel" / f"{rf}.md"
    _atomic_write(dest, "".join(body))
    return dest


def write_offers(out: Path, rf: str, o: dict) -> Path:
    body = [_header(rf, "Accepted-offer comp actuals (ATS)")]
    body.append(
        "ATS accepted-offer actuals. Precedence: BELOW a comp-system approved "
        "band; use as the market spread *around* the band, not as the band.\n\n"
    )
    body.append("| Level | n | Min | Median | Max |\n|---|---|---|---|---|\n")
    for r in o["levels"]:
        body.append(
            f"| {r['level']} | {r['n']} | {r['min']:.0f} | "
            f"{r['median']:.0f} | {r['max']:.0f} |\n"
        )
    dest = out / "internal" / "comp" / f"offers-{rf}.md"
    _atomic_write(dest, "".join(body))
    return dest


def write_tth(out: Path, rf: str, t: dict) -> Path:
    body = [_header(rf, "Time-to-hire (house actuals)", f"closed reqs n={t['n']}")]
    body.append(
        f"- Median time-to-hire: **{t['median_days']} days** "
        f"(min {t['min_days']}, max {t['max_days']}, n={t['n']})\n"
    )
    dest = out / "internal" / "tth" / f"{rf}.md"
    _atomic_write(dest, "".join(body))
    return dest


def write_postings(out: Path, rf: str, p: dict) -> Path:
    body = [_header(rf, "Prior posting language")]
    for i, post in enumerate(p["posts"], 1):
        body.append(f"## {i}. {post['title']}  ({post['updated_at']})\n\n")
        body.append(post["content"] + "\n\n")
    dest = out / "internal" / "postings" / f"{rf}.md"
    _atomic_write(dest, "".join(body))
    return dest


def write_interview(out: Path, rf: str, iv: dict) -> Path:
    body = [_header(rf, "Scorecard attributes (structure)")]
    body.append(
        "Competency fields of record from ATS scorecards; A06's matrix must be "
        "a superset of these. Structure only, no candidate scores.\n\n"
    )
    for a in iv["attributes"]:
        body.append(f"- {a}\n")
    dest = out / "internal" / "interview" / f"{rf}.md"
    _atomic_write(dest, "".join(body))
    return dest


# ---------------------------------------------------------------------------- main
def gather(source, rows, only_rf):
    jobs = source.collection("jobs")
    job_family = {}
    for j in jobs:
        rf = match_family(j, rows)
        if rf and (not only_rf or rf == only_rf):
            job_family[j.get("id")] = rf

    def by_family(records):
        out = {}
        for r in records:
            for jid in _job_ids_of(r):
                rf = job_family.get(jid)
                if rf:
                    out.setdefault(rf, []).append(r)
                    break
        return out

    apps = by_family(source.collection("applications"))
    offers = by_family(source.collection("offers"))
    posts = by_family(source.collection("job_posts"))
    cards = by_family(source.collection("scorecards"))
    jobs_by_family = {}
    for j in jobs:
        rf = job_family.get(j.get("id"))
        if rf:
            jobs_by_family.setdefault(rf, []).append(j)
    families = sorted(set(job_family.values()))
    return families, apps, offers, posts, cards, jobs_by_family


def cmd(args):
    crosswalk = Path(args.crosswalk)
    if not crosswalk.exists():
        die(f"crosswalk not found: {crosswalk}")
    rows = load_crosswalk(crosswalk)
    if not rows:
        die(f"crosswalk has no usable rows: {crosswalk}")
    out = Path(args.out).resolve()

    if args.dry_run:
        print(f"[dry-run] provider={args.provider} out={out}")
        print(
            f"[dry-run] crosswalk: {len(rows)} role families "
            f"({', '.join(r['role_family'] for r in rows)})"
        )
        print(
            "[dry-run] would read Harvest collections: jobs, applications, offers, "
            "job_posts, scorecards"
        )
        print(
            "[dry-run] would write (per family, when non-empty): "
            "internal/funnel, internal/comp/offers-*, internal/tth, "
            "internal/postings, internal/interview"
        )
        print("[dry-run] no network call made, no files written.")
        return

    if args.fixture:
        source = FixtureSource(Path(args.fixture))
    else:
        key = os.environ.get(ENV_KEY)
        if not key:
            die(f"{ENV_KEY} not set in environment (never pass the key as a flag)")
        source = LiveSource(key)

    families, apps, offers, posts, cards, jobs_by_family = gather(
        source, rows, args.role_family
    )
    log.info(
        "fetch: provider=%s, %d crosswalk row(s), %d matched role family(ies)",
        args.provider,
        len(rows),
        len(families),
    )

    written = []
    for rf in families:
        f = build_funnel(apps.get(rf, []))
        if f:
            written.append(write_funnel(out, rf, f))
        o = build_offers(offers.get(rf, []))
        if o:
            written.append(write_offers(out, rf, o))
        t = build_tth(jobs_by_family.get(rf, []))
        if t:
            written.append(write_tth(out, rf, t))
        p = build_postings(posts.get(rf, []))
        if p:
            written.append(write_postings(out, rf, p))
        iv = build_interview(cards.get(rf, []))
        if iv:
            written.append(write_interview(out, rf, iv))

    log.info("fetch: wrote %d KB file(s) under %s", len(written), out)
    if not written:
        print(
            "No Greenhouse signal matched the crosswalk; wrote nothing "
            "(agents fall back to the public/Oracle layer)."
        )
        return
    print(f"Wrote {len(written)} KB file(s) under {out}:")
    for w in written:
        print(f"  {w}")


def build_parser():
    p = argparse.ArgumentParser(
        prog="ats_fetch.py",
        description="Greenhouse Harvest -> Talent One KB writer (aggregate, PII-free).",
    )
    p.add_argument(
        "--provider",
        default="greenhouse",
        choices=["greenhouse"],
        help="ATS provider (only greenhouse implemented)",
    )
    p.add_argument(
        "--crosswalk",
        required=True,
        help="role-family crosswalk CSV (role_family,gh_department,gh_title_match)",
    )
    p.add_argument(
        "--out", required=True, help="KB root to write into (the operator kb_root)"
    )
    p.add_argument("--role-family", help="limit the run to a single role-family key")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan; make no network call and write nothing",
    )
    p.add_argument(
        "--fixture",
        help="read canned Harvest JSON from this dir instead of the network",
    )
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    runlog.setup()
    cmd(args)


if __name__ == "__main__":
    runlog.run(main)
