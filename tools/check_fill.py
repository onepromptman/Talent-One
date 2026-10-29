#!/usr/bin/env python3
"""Talent One fill-contract linter for rendered artifacts.

Checks one rendered artifact (the HTML `skills/talent-one/scripts/render.py render`
writes) against the content contract in `skills/talent-one/references/00_SHARED_CORE.md`
and the slot types in `SLOT_SCHEMA.json`. Stdlib only, no dependencies.

    python3 tools/check_fill.py <run folder>/03_atlas.html \
        --template skills/talent-one/references/templates/TK_03_Talent_Map.dc.html \
        --handoffs <run folder>/handoffs.json --artifact 03

Exit code 0 = clean, 1 = at least one ERROR. Warnings never fail the run.

It is additive to `render.py verify`, which already blocks em dashes, forbidden
phrases, single-value bar widths, surviving example text, empty repeats and pill
vocabulary. This linter adds: range, donut, heat-grid and quadrant bar forms; raw hex
outside the template's declared ramp; hedged optional blocks; repeat counts against
`data-count`; the rendered `handoff.produces` against the renderer's compat
`handoffs.json`; slot value types from `SLOT_SCHEMA.json`; and the 80-word prose
density budget. `tools/check_kit.sh` runs it over a whole run folder.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = MODULE / "skills" / "talent-one" / "references" / "SLOT_SCHEMA.json"
# The design system's primary token, whatever its prefix (a renamed token set still
# encodes the strongest heat band through `var(--<prefix>-primary)`).
PRIMARY_TOKEN = re.compile(r"VAR\(--[A-Z0-9]+-PRIMARY\)")

# The only literals the contract allows in a body: the chart ramp tints.
# Everything else must resolve through a design-system var(--*) token. Each template
# declares its own ramp in a leading style comment, which is authoritative for
# that file; this is the floor every file gets.
BASE_HEX = {
    "#F0EDE6",
    "#DCE6F2",
    "#7FA5CC",
    "#FBF9F4",
    "#EEF6F1",
    "#BFDCCB",
    "#F9EFEF",
    "#F6E4E4",
    "#EDE8DE",
    "#FAF0E6",
    "#E3CDB4",
    "#C9D6E6",
    "#E3C4C4",
    "#FFFFFF",
    "#FFF",
    "#000000",
    "#000",
}


def declared_ramp(src):
    """Tints the file itself declares in its `derived ramp tints` comment."""
    m = re.search(r"derived ramp tints.*?\*/", src, re.DOTALL)
    found = set(re.findall(r"#[0-9A-Fa-f]{3,6}", m.group(0))) if m else set()
    return BASE_HEX | {h.upper() for h in found}


HEDGE_PATTERNS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"\bN/?A\b",
    r"data not available",
    r"not available",
    r"varies by (market|region|company)",
    r"\[insert",
    r"\bplaceholder\b",
    r"coming soon",
    r"to be determined",
]

# Unambiguous recruiter fluff. No legitimate technical reading.
FORBIDDEN_HARD = [
    "i hope this finds you well",
    "came across your profile",
    "exciting opportunity",
    "quick question",
    "touch base",
    "pick your brain",
    "rockstar",
    "best in class",
    "fast-paced environment",
    "competitive salary",
    "world-class",
    "passionate about",
    "circle back",
    "per my last email",
    "synergy",
    "just following up",
    "low-hanging fruit",
    "move the needle",
    "wear many hats",
    "crushing it",
]

# Banned as marketing filler, but each has a legitimate technical sense
# ("robust firmware", "leverage a fixture"). Flag for a human, do not fail.
FORBIDDEN_SOFT = ["leverage", "robust", "seamless", "ninja", "guru", "dynamic team"]

VOID = {"br", "hr", "img", "input", "link", "meta", "source", "col"}


class Node:
    __slots__ = ("attrs", "children", "parent", "tag", "text")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.parent = parent
        self.text = []

    def inner_text(self):
        out = list(self.text)
        for c in self.children:
            out.append(c.inner_text())
        return " ".join(t for t in out if t).strip()

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:
            self.cur = node.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.text.append(data.strip())


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, check, msg):
        self.rows.append((level, check, msg))

    def error(self, check, msg):
        self.add("ERROR", check, msg)

    def warn(self, check, msg):
        self.add("WARN", check, msg)

    @property
    def errors(self):
        return [r for r in self.rows if r[0] == "ERROR"]


def parse(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    d = DOM()
    d.feed(src)
    return src, d.root


def style_of(node):
    return node.attrs.get("style", "")


def pct(style, prop):
    """First `prop:<n>%` in an inline style, as a 0-1 float.

    Accepts a unitless zero: `left:0` is valid CSS and means 0%.
    """
    m = re.search(rf"(?:^|[;\s]){prop}\s*:\s*([\d.]+)%", style)
    if m:
        return float(m.group(1)) / 100
    if re.search(rf"(?:^|[;\s]){prop}\s*:\s*0\s*(?:;|$)", style):
        return 0.0
    return None


def check_bars(root, rep):
    TOL = 0.015  # 1.5 percentage points
    for n in root.walk():
        raw = n.attrs.get("data-bar")
        if raw is None:
            continue
        style = style_of(n)
        vals = [v.strip() for v in raw.split(",")]
        try:
            nums = [float(v) for v in vals]
        except ValueError:
            rep.error("bar-geometry", f'data-bar="{raw}" is not numeric')
            continue
        for v in nums:
            if not 0 <= v <= 1:
                rep.error("bar-geometry", f'data-bar="{raw}" outside 0-1')

        # donut / conic. Scope to inside conic-gradient(...) so an unrelated
        # border-radius:50% on the same element is not mistaken for a stop.
        if "conic-gradient" in style:
            inner = re.search(r"conic-gradient\(([^)]*)\)", style)
            stops = re.findall(r"([\d.]+)%", inner.group(1)) if inner else []
            if stops and abs(float(stops[0]) / 100 - nums[0]) > TOL:
                rep.error(
                    "bar-geometry",
                    f'data-bar="{raw}" but conic first stop is {stops[0]}%',
                )
            continue

        # heat-grid cell: encodes strength by BACKGROUND, not width
        # (00_SHARED_CORE.md section 5.3). Verify the colour band instead.
        bg = re.search(r"background\s*:\s*([^;]+)", style)
        if bg and pct(style, "width") is None and "min-height" in style:
            colour = bg.group(1).strip().upper().replace(" ", "")
            v = nums[0]
            want = (
                "var(--*-primary)"
                if v >= 0.9
                else "#7FA5CC"
                if v >= 0.5
                else "#DCE6F2"
                if v >= 0.15
                else "#F0EDE6"
            )
            ok = (
                PRIMARY_TOKEN.search(colour) is not None if v >= 0.9 else want in colour
            )
            if not ok:
                rep.error(
                    "heat-encoding",
                    f'heat cell data-bar="{raw}" wants {want}, has {bg.group(1).strip()}',
                )
            continue

        # range: left + width
        if len(nums) == 2:
            left, width = pct(style, "left"), pct(style, "width")
            if left is None or width is None:
                rep.error(
                    "bar-geometry",
                    f'range data-bar="{raw}" needs inline left% and width%, got "{style[:60]}"',
                )
                continue
            if abs(left - nums[0]) > TOL:
                rep.error(
                    "bar-geometry", f'data-bar="{raw}" start {nums[0]} vs left {left}'
                )
            if abs(width - (nums[1] - nums[0])) > TOL:
                rep.error(
                    "bar-geometry",
                    f'data-bar="{raw}" span {nums[1] - nums[0]:.3f} vs width {width}',
                )
            continue

        # quadrant point: positioned by left+top, value is not a width
        if pct(style, "top") is not None and pct(style, "width") is None:
            if pct(style, "left") is None:
                rep.error(
                    "bar-geometry",
                    f'quadrant point data-bar="{raw}" has top but no left',
                )
            continue

        # bubble: sized in px, not verifiable against a fraction
        if re.search(r"width\s*:\s*[\d.]+px", style):
            continue

        # single value: width
        width = pct(style, "width")
        if width is None:
            rep.error(
                "bar-geometry",
                f'data-bar="{raw}" has no inline width% (style="{style[:60]}")',
            )
        elif abs(width - nums[0]) <= TOL:
            pass
        elif width > nums[0]:
            # Over-draw. A legibility floor on a tiny funnel stage is a known
            # practice and the true number is printed alongside, so this is a
            # judgment call for a human, not an automatic failure.
            rep.warn(
                "bar-geometry",
                f'data-bar="{raw}" drawn at {width:.2f} (over-drawn, likely a legibility floor)',
            )
        else:
            # Under-draw misrepresents the number downward. Never acceptable.
            rep.error(
                "bar-geometry",
                f'data-bar="{raw}" drawn at only {width:.2f}; the bar understates the number',
            )


def check_repeats(root, rep):
    for n in root.walk():
        name = n.attrs.get("data-repeat")
        if name is None:
            continue
        kids = [c for c in n.children if c.tag not in VOID]
        if not kids:
            rep.error("empty-repeat", f'data-repeat="{name}" has no children')
            continue
        spec = n.attrs.get("data-count")
        if not spec:
            continue
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", spec)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        elif spec.strip().isdigit():
            lo = hi = int(spec.strip())
        else:
            continue
        if not lo <= len(kids) <= hi:
            rep.warn(
                "count-range",
                f'data-repeat="{name}" has {len(kids)} children, data-count="{spec}"',
            )


def check_optional(root, rep):
    for n in root.walk():
        if "data-optional" not in n.attrs:
            continue
        txt = n.inner_text()
        for pat in HEDGE_PATTERNS:
            if re.search(pat, txt, re.IGNORECASE):
                rep.error(
                    "hedged-optional",
                    f"data-optional block hedges instead of being deleted: "
                    f'"{txt[:70]}"',
                )
                break


def slot_map(root):
    out = {}
    for n in root.walk():
        s = n.attrs.get("data-slot")
        if s is not None:
            out.setdefault(s, []).append(n.inner_text())
    return out


def check_unfilled(root, template_root, rep):
    filled, shipped = slot_map(root), slot_map(template_root)
    # Header/label slots legitimately keep the shipped wording; kit.mark and the
    # footer are renderer-owned chrome.
    exempt = {"kit.mark", "doc.title", "doc.eyebrow", "footer.left", "footer.right"}
    stale = []
    for slot, vals in filled.items():
        if slot in exempt or slot not in shipped:
            continue
        for v in vals:
            if len(v) > 25 and v in shipped[slot]:
                stale.append(slot)
                break
    for slot in sorted(set(stale)):
        rep.error(
            "unfilled-slot", f'data-slot="{slot}" still holds the shipped example text'
        )


def body_region(src):
    """Everything after the </style> that closes the helmet block."""
    i = src.rfind("</style>")
    return src[i:] if i != -1 else src


def check_hex(src, rep):
    allowed, seen = declared_ramp(src), set()
    for m in re.finditer(r"#[0-9A-Fa-f]{3,6}\b", body_region(src)):
        h = m.group(0).upper()
        if h not in allowed and h not in seen:
            seen.add(h)
            rep.error(
                "raw-hex", f"{m.group(0)} is not a sanctioned ramp tint; use a token"
            )


def check_text(root, rep):
    # A banned-terms list legitimately contains the banned terms. Exclude any
    # subtree whose data-repeat or data-slot names it as such.
    def scannable(n):
        # Inlined design-system CSS and scripts are not body text.
        if n.tag in ("style", "script", "head", "title"):
            return False
        for a in ("data-repeat", "data-slot"):
            v = n.attrs.get(a, "")
            if v.startswith(("banned", "cheat.bad")):
                return False
        return True

    def collect(n):
        if not scannable(n):
            return []
        out = list(n.text)
        for c in n.children:
            out.extend(collect(c))
        return out

    text = " ".join(t for t in collect(root) if t)
    if "—" in text:
        n = text.count("—")
        rep.error("em-dash", f"{n} em dash(es) in body text; the kit bans them")
    low = text.lower()

    def used_unquoted(phrase):
        """True if the phrase is used, rather than quoted as a bad example.

        These artifacts teach by negative example ("never write 'exciting
        opportunity'"), so a phrase inside straight double quotes is the
        artifact doing its job, not violating the voice rule.
        """
        for m in re.finditer(rf"\b{re.escape(phrase)}\b", low):
            before, after = low[: m.start()], low[m.end() :]
            # Quoted if there is an unclosed opening quote just before it.
            if before.count('"') % 2 == 1 and '"' in after:
                continue
            return True
        return False

    for p in FORBIDDEN_HARD:
        if used_unquoted(p):
            rep.error("forbidden-phrase", f'"{p}"')
    for p in FORBIDDEN_SOFT:
        if used_unquoted(p):
            rep.warn(
                "forbidden-phrase", f'"{p}" (check: filler, or a real technical use?)'
            )


def handoff_entry(handoffs_path, artifact, legacy_path):
    """The produced-key list the renderer recorded for this artifact.

    `--handoffs` is the compat `handoffs.json` render.py writes into a run folder,
    keyed by artifact number; each entry's `handoff` is either the flat shape
    (`produces` as one " · "-joined string) or the keys shape (the produced keys
    themselves). `--handoff` reads a single legacy `{"handoff": {...}}` file."""
    if handoffs_path:
        with open(handoffs_path, encoding="utf-8") as fh:
            data = json.load(fh)
        h = (data.get(artifact) or {}).get("handoff")
        if h is None:
            return None
    else:
        with open(legacy_path, encoding="utf-8") as fh:
            h = json.load(fh).get("handoff", {})
    if isinstance(h.get("produces"), str):
        return [k.strip() for k in re.split(r"[·|,]", h["produces"]) if k.strip()]
    return [
        k for k in h if k not in ("produces", "consumers", "blocked", "assumptions")
    ]


def check_handoff(root, rep, handoffs_path=None, artifact=None, legacy_path=None):
    slots = slot_map(root)
    produces = slots.get("handoff.produces", [])
    if not produces:
        rep.error("handoff", 'no data-slot="handoff.produces" in the artifact')
        return
    rendered = [k.strip() for k in re.split(r"[·|,]", produces[0]) if k.strip()]
    if not (handoffs_path and artifact) and not legacy_path:
        rep.warn(
            "handoff",
            f"{len(rendered)} keys rendered; pass --handoffs and --artifact to verify",
        )
        return
    actual = handoff_entry(handoffs_path, artifact, legacy_path)
    if actual is None:
        rep.error("handoff", f"no entry for artifact {artifact} in {handoffs_path}")
        return
    norm = lambda ks: [re.sub(r"\[\]$", "", k) for k in ks]
    if norm(rendered) != norm(actual):
        rep.error(
            "handoff",
            f"handoff.produces {norm(rendered)} != recorded handoff keys {norm(actual)}",
        )
    blocked = slots.get("handoff.blocked", [""])[0]
    if not blocked.strip():
        rep.error(
            "handoff", 'handoff.blocked is empty; say "Nothing" or name a blocker'
        )


NUM = r"[\d,]+(?:\.\d+)?"
DASH = r"[-–]"  # hyphen or en dash; em dashes are banned kit-wide

# A superset of tools/extract_slot_schema.py's PATTERNS (the linter also knows
# `delta` and `metric`, and accepts unit words after a count). Kept independent
# (not imported) so this file stands alone; tools/tests/ asserts that every type the
# extractor or SLOT_SCHEMA.json can emit has a pattern here.
TYPE_PATTERNS = {
    "pill": r"^(Sourced|Estimate|Modeled|Internal|Derived)\b",
    "currency_range": rf"^\$?{NUM}\s*[KkMm]?\s*{DASH}\s*\$?{NUM}\s*[KkMm]?$",
    # A numeric range, optionally with a trailing unit phrase: "1-3 warm
    # intros" is still checked on its numeric front half, the words are free.
    "count_range": rf"^{NUM}\s*{DASH}\s*{NUM}(\s+\S.*)?$",
    "currency": rf"^[~<>]?\${NUM}\s*[KkMm]?$",
    "percent": r"^[~<>+-]?[\d.]+\s*%$",
    "ratio": r"^[\d.]+\s*:\s*[\d.]+$",
    "duration": r"^(D\d+|[\d.]+\s*(min|minutes|hr|hours|days?|weeks?|months?|yrs?|years?)|"
    r"days?|weeks?|months?|hours?|minutes?|"  # bare unit word, no number: "Weeks"
    r"[\d.]+\s*/\s*arm|this week|next week|today|"
    r"\d+\s*business\s*days?)$",
    "date": r"^([A-Z]{3}\s+\d{4}|\d{4}|\d{4}-\d{2}-\d{2})$",
    "count": rf"^[~<>+-]?{NUM}\s*[KkMmBb]?\+?(\s*(words|/\s*arm))?$",
    "empty_cell": r"^[-–—]$",
    "delta": rf"^{NUM}\s*(->|→)\s*{NUM}$",
    # A single headline stat whose unit varies by context (%, x, K/M count);
    # only the numeric core is checked. See SLOT_SCHEMA.json's note on
    # pullstat.value for why this is its own type rather than "percent".
    "metric": rf"^[~<>+-]?{NUM}\s*(%|[x×]|[KkMmBb])?$",
}

# Types where free text is the point; nothing to check beyond presence,
# which check_unfilled and the empty-repeat/empty-optional checks already
# cover. Listed explicitly so an unrecognized type in the schema is a loud
# failure (a typo in SLOT_SCHEMA.json) rather than a silent skip.
FREE_TEXT_TYPES = {"label", "prose_short", "prose_long"}


def check_types(root, schema, rep, strict=False):
    """Slot values against SLOT_SCHEMA.json types. Advisory (WARN) by default: in the
    renderer era each artifact's content is already validated against its own
    TK_NN.content-schema.json by `render.py render --strict`, and SLOT_SCHEMA.json keys
    types by slot name across templates (one name can carry a percent in one template
    and a chip in another), so a mismatch here is a prompt for review, not proof of a
    defect. `--strict-types` makes them errors."""
    if schema is None:
        return
    flag = rep.error if strict else rep.warn
    slots = slot_map(root)
    for slot, vals in slots.items():
        spec = schema["slots"].get(slot)
        if spec is None:
            continue  # a slot the schema doesn't know about is not this check's job
        typ = spec["type"]
        if typ == "chip":
            allowed = spec.get("allowed")
            for v in vals:
                v = v.strip()
                if allowed:
                    if not any(v.lower() == a.lower() for a in allowed):
                        flag(
                            "slot-type",
                            f'data-slot="{slot}" is a fixed chip; "{v}" is not '
                            f"in its controlled vocabulary {allowed}",
                        )
                elif v.count(" ") > 3:
                    # An open chip (reused across templates for different
                    # axes, see SLOT_SCHEMA.json's note on this slot): no
                    # fixed list, but it is still a chip, not a sentence.
                    flag(
                        "slot-type",
                        f'data-slot="{slot}" is an open chip but "{v}" reads '
                        f"like prose, not a short tag",
                    )
            continue
        if typ in FREE_TEXT_TYPES:
            continue
        pat = TYPE_PATTERNS.get(typ)
        if pat is None:
            flag(
                "slot-type",
                f'SLOT_SCHEMA.json has an unrecognized type "{typ}" for "{slot}"',
            )
            continue
        for v in vals:
            v = v.strip()
            if v and not re.match(pat, v, re.IGNORECASE):
                flag(
                    "slot-type",
                    f'data-slot="{slot}" is type {typ} (e.g. "{spec.get("example", "")}") '
                    f'but got "{v}"',
                )


def check_density(root, rep):
    for n in root.walk():
        if n.tag == "p":
            words = len(n.inner_text().split())
            if words > 80:
                rep.warn(
                    "density",
                    f"prose block of {words} words exceeds the 80-word budget",
                )


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "doc", metavar="ARTIFACT_HTML", help="the rendered artifact to lint"
    )
    ap.add_argument("--template", help="the TK_*.dc.html this was rendered from")
    ap.add_argument("--handoffs", help="the run folder's compat handoffs.json")
    ap.add_argument("--artifact", help="artifact number (NN) to look up in --handoffs")
    ap.add_argument("--handoff", help='a single legacy {"handoff": {...}} JSON file')
    ap.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="slot type schema for check_types (default: the module's SLOT_SCHEMA.json). "
        "Pass --no-schema to skip type checking entirely.",
    )
    ap.add_argument(
        "--no-schema", action="store_true", help="skip the --schema type check"
    )
    ap.add_argument(
        "--strict-types",
        action="store_true",
        help="make SLOT_SCHEMA.json type mismatches errors, not warnings",
    )
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    ap.add_argument(
        "--reference",
        action="store_true",
        help="file documents the design system rather than carrying a search's "
        "data (TK_00). Palette swatches print token values as literal hex "
        "on purpose, so the raw-hex rule does not apply.",
    )
    args = ap.parse_args()

    src, root = parse(args.doc)
    rep = Report()

    check_bars(root, rep)
    check_repeats(root, rep)
    check_optional(root, rep)
    if not args.reference:
        check_hex(src, rep)
    check_text(root, rep)
    check_density(root, rep)
    check_handoff(root, rep, args.handoffs, args.artifact, args.handoff)
    if not args.no_schema and args.schema:
        try:
            with open(args.schema, encoding="utf-8") as fh:
                schema = json.load(fh)
        except FileNotFoundError:
            schema = None
            rep.warn(
                "slot-type", f"schema {args.schema} not found, skipping type check"
            )
        check_types(root, schema, rep, strict=args.strict_types)
    if args.template:
        _, troot = parse(args.template)
        check_unfilled(root, troot, rep)
    else:
        rep.warn("unfilled-slot", "pass --template to detect unfilled slots")

    for level, check, msg in rep.rows:
        if args.quiet and level != "ERROR":
            continue
        print(f"{level:5} {check:18} {msg}")

    n = len(rep.errors)
    print(f"\n{args.doc}: {n} error(s), {len(rep.rows) - n} warning(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
