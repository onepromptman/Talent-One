# ATS fetch contract: Greenhouse Harvest to a local KB folder

Version 1.1. The spec `ats_fetch.py` implements. Grounded in the module's
`skills/talent-one/references/02_GROUNDING_MATRIX.md` (the `ATS` T0 slot, Part 2
precedence, Part 5 sensitive-data routing) and `CONTEXT_PACK.md` (where house numbers
land in the pack).

## 1. Purpose and boundary

Fill the `ATS` T0 slot with **aggregate, PII-free** house signal, so the research pass
and the agents that lean on internal data ground in real requisition and funnel numbers
instead of the public layer alone:

| Consumer (Talent One 2.x) | What ATS grounds |
|---|---|
| scout (builds `pack.json`) | accepted-offer comp actuals by level (`comp.by_level`); funnel pass-through (`market.funnel`); time-to-hire (`timing`) |
| 02 jdbot | prior posting language for the role family |
| 06 interview-lab, 08 recruiter-screen, 09 interview-coach | scorecard attributes and interview-kit structure |

The tool **writes KB files only**. It changes no agent prompt and no template. The runner
(`talent_kit.py --kb-root <dir>`) adds that folder to every session (`--add-dir`) and names
it in each prompt as a connected internal source, so agents find it with Read/Grep.

## 2. Greenhouse Harvest endpoints and what each yields

Read-only. Harvest base `https://harvest.greenhouse.io`. Auth: HTTP Basic, username =
API key, empty password (`Authorization: Basic base64(key + ":")`). The key comes from
the environment variable `GREENHOUSE_HARVEST_KEY`, never a flag, never committed.

| Endpoint | Yields | Aggregation rule |
|---|---|---|
| `GET /v1/jobs`, `/v1/jobs/{id}` | reqs, departments, offices, opened/closed dates | map to role family via crosswalk; TTF = closed minus opened |
| `GET /v1/job_posts` | posting text | last N posts per role family (prior JD language) |
| `GET /v1/applications?job_id=` | applications by stage | **count only**, per stage, per role family; never store candidate objects |
| `GET /v1/offers` | offer status + amount + level | **counts + comp stats** (min/median/max) by level; strip candidate identity |
| `GET /v1/scorecards` | scorecard attributes | structure only (competency field names); no candidate scores, no free text |

Pagination: `?per_page=500&page=N`, follow until a short page. Rate limit: Harvest is
about 50 requests per 10 seconds; on `429` back off exponentially and retry; **never
retry any other 4xx**.

## 3. KB output layout

Written under `<kb_root>/`. One file per role family per signal. Every file is Markdown
with a header block carrying the provenance pill, the crosswalk key, the as-of date, and
the n counts.

| Path | Content |
|---|---|
| `internal/funnel/<rf>.md` | pass-through % + **n per stage** |
| `internal/comp/offers-<rf>.md` | accepted-offer comp stats by level (aggregate) |
| `internal/tth/<rf>.md` | time-to-hire, interviews-per-hire actuals |
| `internal/postings/<rf>.md` | prior posting language (last N) |
| `internal/interview/<rf>.md` | scorecard attributes / kit structure |

`<rf>` = role-family key from the crosswalk (section 7). **`offers-*.md` holds ATS
accepted-offer actuals, which sit BELOW a comp-system approved band in Part 2
precedence**: it is never written to `internal/comp/bands.csv` (that path is reserved for
the comp-system band export). Keeping the two files distinct keeps the precedence rule
legible.

## 4. Provenance and basis

- Every quantitative value carries `Sourced · Greenhouse YYYY-MM-DD` (the pull date).
- **Where Greenhouse is silent, write nothing**: no row, no zero-fill. A missing file
  makes agents fall back to the Estimate path, which is the supported standalone
  behaviour. Never a `Sourced` pill over absent data.
- Funnel and comp files report the raw **n** beside each rate. The tool does **not**
  decide house versus benchmark; it reports n and the agent applies the Part 2 `n >= 30`
  rule.

## 5. PII and data-handling guardrails (a violation is a build failure)

1. **No candidate PII, ever.** No candidate name, email, phone, or any candidate-object
   field enters a KB file. Only aggregate counts and de-identified comp statistics. The
   tests assert this against fixtures that deliberately carry candidate names and emails.
2. **A comp level is emitted only at or above `MIN_COMP_N` (3) offers**, so a single
   offer cannot be re-identified.
3. **T0 data never leaves T0 except into KB files.** The tool makes no web call other
   than to Harvest and puts no internal string into any outbound query.
4. **Never write into a repository.** `<kb_root>` for a real pull is a private,
   gitignored location; fetched data never lands in this repo.
5. The API key is read from the environment only and is masked (last 4 characters)
   anywhere it is logged.

## 6. Runner integration

`talent_kit.py` takes `--kb-root <dir>` (or `resources.kb_root` in an optional runner
`--config` file, resolved relative to that file by a constrained line scan, no YAML
library). When it resolves and exists, the runner adds it to every session with
`--add-dir` and lists it in the prompt as a connected internal source.

## 7. Crosswalk (your binding, not part of this repo)

The tool is keyed by a **role-family crosswalk**: a CSV mapping Greenhouse
department/job-title to a role-family key. Only a synthetic example ships
(`tests/fixtures/greenhouse/crosswalk.csv`); your real crosswalk is your own work content
and stays out of this repo.

```
role_family,gh_department,gh_title_match
controls,Controls,*Controls*
embedded_sw,Firmware,*Embedded*|*Firmware*
```

## 8. Tool interface

```
python3 ats_fetch.py --provider greenhouse \
    --crosswalk <crosswalk.csv> --out <kb_root> \
    [--role-family <rf>] [--dry-run] [--fixture <dir>]
```

- Zero third-party dependencies (`urllib`, stdlib only).
- `--dry-run`: print the planned requests and output paths; make no network call.
- `--fixture <dir>`: read canned Harvest JSON from `<dir>` instead of the network; the
  offline path the tests drive.
- Idempotent: each run overwrites its KB files atomically.

## 9. Editions

Only this Python edition ships here. There is no n8n edition of the fetch in this repo.
