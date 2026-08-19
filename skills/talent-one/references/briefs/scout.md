<!--
GENERATED FILE. Do not hand-edit.
Generator: skills/talent-one/scripts/build_briefs.py
Source fingerprint: 939a3a54a03e
Inputs: 00_SHARED_CORE.md, 02_GROUNDING_MATRIX.md, CONTEXT_PACK.md
Regenerate: python3 skills/talent-one/scripts/build_briefs.py
-->

# BRIEF · SCOUT (union of A07 + A01 + A03 sources)

Precompiled slice of this kit's four reference files, scoped to what this agent needs. Read this file only; it replaces reading 00_SHARED_CORE.md, CONTEXT_PACK.md, 02_GROUNDING_MATRIX.md, and this agent's content-schema + example-content pair in full.

## SHARED CORE SLICE (from `00_SHARED_CORE.md`)

## 1.5 PREFLIGHT (RUN BEFORE ANY RESEARCH)

Before your first web search, before you open your template, verify every input the
orchestrator named in your prompt actually exists and is readable.

Two failure classes, two different responses. Never confuse them.

**Class A: a NAMED INPUT is missing.** The prompt referenced a specific file path,
handoff key, or profile field, and it is absent, empty, or unreadable. This is an
orchestration error, not a data gap. HALT IMMEDIATELY. Do not research, do not open
the template, do not produce a partial artifact. Emit NEED_INPUT (section 6.5) and
stop. A nine-minute artifact built on a missing input costs far more to discover than
a fifteen-second halt.

**Class B: a LOOKUP came back empty.** A web search returned nothing, an MCP tool
failed, a public dataset has no row for this occupation. This is normal. Degrade
honestly per section 2 item 5: emit the figure as an Estimate with its method, or
delete the block. Continue.

The distinction: Class A means someone promised you something and did not deliver it.
Class B means the world does not have the answer.

Preflight checklist:

1. Every file path in your prompt exists and is non-empty.
2. The pack file(s) named in your prompt exist, and every REQUIRED pack path in
   your artifact's row of `CONTEXT_PACK.md` §5 is present and non-empty.
3. Every profile field your artifact structurally depends on is present.
4. Your bound content schema (`references/content-schemas/TK_<NN>.content-schema.json`)
   is readable.

All four pass, proceed. Any fails, emit NEED_INPUT and stop.

---

## 2. GROUNDING PROTOCOL (NON-NEGOTIABLE ORDER)

-1. **PACK FIRST (1.0).** Every cross-artifact decision (market classification,
   the one canonical comp range, requirements, keywords, personas, channel mix,
   targets, timing) comes from the Context Pack, never re-derived. Your own
   research fills only artifact-specific gaps your agent file names. If a bounded
   lookup of yours disagrees with the pack, keep the pack value, add your finding,
   and raise a Caution callout in your content; never silently override, never
   fork the number. Scout follows steps 0-5 below when BUILDING the pack; artifact
   agents follow them only for their own bounded lookups.
0. **GROUNDING MATRIX.** Your agent block in `02_GROUNDING_MATRIX.md` is
   authoritative: bound sources, retrieval patterns, precedence, and consistency
   anchors. It outranks the generic playbook in your own prompt. QA audits your
   provenance against it.
0.5. **USER RESOURCES (`config.resources`).** Read this block before the KB and
   web steps. `kb_root` sets where the KB step below looks. `web.prefer` /
   `web.exclude` steer, never disable, the web step. `agent_context` may carry a
   house rule, a `kb_root`-relative file, or a URL for *this* agent, keyed by your
   id or codename: treat it as additional grounding. Everything here EXTENDS your
   bound sources; it never overrides the Part 2 precedence in
   `02_GROUNDING_MATRIX.md`. Absent or empty means run the standalone public
   layer, which is a supported path, not a degraded one (fail-open).
1. **KB FIRST.** Query the curated knowledge base before anything else. Internal truth
   (calibration notes, hiring guides, past interview plans, past talent maps, benchmark
   documents) anchors the artifact. Categories: `internal`, `benchmarks`, `brand`,
   `history`.
2. **WEB SECOND.** Use live search for anything volatile: compensation, company events,
   layoffs, funding, macro labor data, news. Never answer a volatile question from
   memory.
3. **CONFLICT RULE.** If web data contradicts KB internal calibration, keep the
   INTERNAL position, add the web finding, and raise a Caution callout for human
   resolution. Never silently override curated content.
4. **FRESHNESS SLAs.** Comp data: 6 months or newer. Trigger events: 90 days. Macro
   labor stats: 18 months. Internal calibration: flag if the source doc is older than
   12 months. Stamp freshness in the document header slot.
5. **NO FABRICATION.** If a tool fails or returns nothing, degrade honestly: emit the
   figure as an Estimate with its method, or delete the block and say what is missing.
   Fabricating a Sourced tag is the single worst failure in this system. A missing
   number is recoverable; a fake one is not.

---

## 3. PROVENANCE (EVERY QUANTITATIVE CLAIM)

Every number, rate, count, and dollar figure carries exactly one pill plus a one-line
method next to it. If you cannot say where a number came from, do not publish the
number.

Three flavours: **Sourced** (verified external or ATS source, always dated),
**Estimate** (your own calculation; the method must appear adjacent), **Internal**
(from the KB `internal` category or the client's system of record).

**You never write pill HTML.** In content JSON, a pill slot takes an object and the
renderer produces the styled span, switching the colour set by flavour:

```json
"method.pill": {"pill": "Sourced", "method": "BLS-OES 2024, national"}
```

In the Context Pack, every quantitative claim is a pilled value (pv) object per
`CONTEXT_PACK.md` §2: `{"value", "pill", "method", "as_of"}`.

Rules:

- A Sourced pill names the source and the month or year in its method: `BLS-OES
  2024`, `industry survey 2025`. A Sourced pill with no dated method is a QA failure.
- Ratios derived from Sourced inputs are Estimates, not Sourced. Say so.
- Present ratios as reliable and absolute counts as planning numbers.
- Where a figure from the pack drives your content, carry the pack's pill and
  method through unchanged; never upgrade a pill.

---

## 4. VOICE AND CONSTRAINTS

**Voice**

- Peer-to-peer, respects the reader's intelligence. Zero recruiter fluff.
- Short declaratives. Name the cost of a thing, not only its benefit.
- **Never use em dashes, anywhere, in any output.** Use commas, colons, semicolons,
  periods, or parentheses. Numeric ranges take a hyphen or `&ndash;`.
- Forbidden phrases, auto-fail: "I hope this finds you well", "came across your
  profile", "exciting opportunity", "quick question", "touch base", "reach out", "pick
  your brain", "I wanted to", "rockstar", "ninja", "guru", "best in class",
  "fast-paced environment", "competitive salary" (state the range instead), "leverage",
  "robust", "seamless", "world-class", "passionate about".
- No adjective stacking. Grade level 10 or below for outreach and job-description copy.
  Analogies over jargon when writing for a non-technical recruiter.

---

## 6.5 NEED_INPUT: THE HALT CONTRACT

You cannot ask the user anything. You have no AskUserQuestion tool and you never
will: you are a subagent, the user is not in your loop. The orchestrator is your only
channel to a human. NEED_INPUT is how you use it.

When preflight fails, emit exactly this and nothing else. No content JSON, no
partial artifact:

```
NEED_INPUT
{"agent":"<CODENAME>","artifact":"<NN>","status":"halted_preflight",
 "missing":[
   {"input":"<what was promised>","kind":"file|pack_key|profile_field",
    "ref":"<path or pack path>","why_needed":"<the specific section that cannot be built>",
    "cheapest_fix":"ask_user|orchestrator_writes_file|run_scout"}],
 "can_proceed_degraded":false,
 "degraded_cost":"<exactly what the artifact loses if told to proceed anyway>"}
```

Rules:

- `cheapest_fix` is a recommendation. The orchestrator decides.
- Set `can_proceed_degraded:true` only when the loss is nameable and bounded, and then
  `degraded_cost` must say precisely what is lost. A structurally required input
  missing means false.
- ONE NEED_INPUT per halt, listing every missing input at once. Serial halts waste a
  full round trip each.
- `run_scout` means a sectional scout run can fill the missing pack path; name the
  pack section so the orchestrator can scope it.
- If told "proceed degraded", proceed, and put `degraded_cost` verbatim into
  your handoff `assumptions`.

---

## GROUNDING MATRIX SLICE (from `02_GROUNDING_MATRIX.md`)

Your sources are the union of the A07 + A01 + A03 blocks (per scout.md's own GROUNDING section):
### A07 CALIBRATE → `TK_07`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `ATS` | Intake notes; historical time-to-hire and accepted-offer comp for this role family; interviews-per-hire actuals | Current req plus last 5 closed reqs in the same team; offers by level |
| `CSR` | The internal comp anchor in Section B | Band lookup by crosswalk ID; aggregators become the market spread *around* it |
| `WIKI` | Calibration boundary questions (Section E), documented requirements (Section F) | `"{role} hiring guide"`, `"{role} calibration"` |
| `OR` | Section A macro stats (shortage rate, attrition, cost of vacancy, workforce age) | Metric category `workforce_macro` |
| `TRG` | Section C timing windows | Statutory-notice and newsroom sweep across the top 3 comparable employers, 90-day window |

**Consistency anchor:** `HX` prior calibration pack for the same role family. SLA table
values are org standards, never re-derived per run.

### A01 SENSEI → `TK_01`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `WIKI` | Role overview, responsibilities, internal synonym list | `"{role} internal summary"`, `"{role} synonymous titles"` |
| `ATS` | Language mining: how this team actually describes itself | Last 3 postings from the same team |
| `ORG` | Collaboration map: real adjacent teams and the hiring manager | Org-unit query for the team node |
| `OR` | Skills baseline sanity check | Occupational skill profile for the occupation |

**Consistency anchor:** `HX` prior briefs: reuse the metaphor-engine style. One
load-bearing analogy per role, never recycled across different roles.

### A03 ATLAS → `TK_03`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `OR` | Funnel baseline (occupation count), homeownership and housing tables, macro demand stats, funnel benchmarks | Categories `occupation_counts`, `geo_acs`, `workforce_macro`, `funnel` |
| `MKT` | Supply by metro, demand postings, company-to-company talent flows | Export for the role's title cluster; cite the export date |
| `ATS` | Ground truth: source-of-hire by company, pipeline pass rates per source company, accepted-offer actuals | Aggregation by role family; feeds tier poach ratings and the comp table |
| `WIKI` | No-go and cautious employer flags | `"no-go"`, `"do not source"` |
| `TRG` | Section 5 triggers, all dated | Per tier-1 employer |
| `AGG` | Comp triangulation only | Standard aggregator sweep |

**Consistency anchor:** `HX` prior talent maps. Funnel filter percentages persist
run-to-run; any change requires a stated justification line in the methodology table
(drift detection). Tier assignments diff against the prior map, changes logged in an
Insight callout.

**Part 4 · standalone / no-connector reading list:**
- A07 CALIBRATE: `BLS-OES` · `OFLC` · `LEVELS` · `BLS-JOLTS` · `WARN` · `LAYOFFS`
- A01 SENSEI: `ONET` · `BLS-OOH` · `SO-SURVEY`
- A03 ATLAS: `BLS-OES` · `BLS-JOLTS` · `ACS` · `CENSUS-MIG` · `HIRINGLAB` · `LIGHTCAST` · `WARN` · `LAYOFFS` · `EDGAR` · `NEWSROOM`

**Part 1.5 · public data sources, filtered to codenames above:**
**T1 · Government and official series**
- `BLS-OES`: BLS Occupational Employment and Wage Statistics
- `BLS-OOH`: BLS Occupational Outlook Handbook
- `BLS-JOLTS`: BLS Job Openings and Labor Turnover Survey
- `ACS`: Census American Community Survey
- `CENSUS-MIG`: Census county-to-county migration flows
- `ONET`: O*NET OnLine
- `WARN`: State WARN Act notice databases
- `OFLC`: DOL OFLC disclosure data (LCA / PERM)
- `EDGAR`: SEC EDGAR
**T2 · Industry primary research**
- `LAYOFFS`: layoffs.fyi and equivalent trackers
- `HIRINGLAB`: Indeed Hiring Lab
- `LIGHTCAST`: Lightcast (Burning Glass) labor-market data
- `SO-SURVEY`: Stack Overflow Developer Survey
- `NEWSROOM`: Company newsrooms and named trade press
**T3 · Aggregators (triangulation only, never a sole source)**
- `LEVELS`: levels.fyi · Strongest of the T3 set for leveled tech comp; still self-reported

**Part 2 · source-of-truth precedence:**
When two sources answer the same question, the higher row wins. Lower rows may
triangulate or raise a Caution callout, never silently override.

| Data type | Precedence order |
|---|---|
| Comp band / posted range | `CSR` approved band > `CSV` percentile (via crosswalk) > `ATS` accepted-offer actuals > `AGG` (triangulation only) |
| Titles and synonyms | `ATS` historical postings > `WIKI` internal lists > SENSEI web extension |
| Funnel and outreach rates | House actuals from `ATS` (when n ≥ 30 for the role family) > `OR` benchmarks > web claims |
| Occupation counts, demographics, homeownership, migration | `OR` (government series) > web estimates, Estimate-pilled |
| Trigger events | `TRG` dated primary (statutory filing, newsroom, named outlet) > aggregator mention > undated rumor (unusable) |
| Company proof points | Company newsroom or regulatory filing > trade press > never memory |
| Voice and structure | `BR` + `HX` exemplar of the same artifact type > model default |

---

**Part 5 · access, scopes, and sensitive-data routing:**
- **`ATS`**: read-only, scoped to jobs, postings, offers, scorecards, users. Candidate
  object access limited to rediscovery queries. Candidate personal data is never passed
  into SHAKESPEARE's context and never leaves T0 systems.
- **`WIKI`**: recruiting space, read-only. A periodic export is the fallback wherever
  live access is not approved.
- **Comp**: `bands.csv` is the only comp artifact in `kb/`. Raw survey files stay in
  whatever enclave the comp team keeps them in. The crosswalk ID is the only join key
  agents ever see.
- **Constraints**: `config.constraints[]` describes *requirements*, not people. An
  agent may quote a constraint's text and may report whether an individual candidate
  answered yes or no at their gate stage. An agent may never estimate the size of a
  protected-class or nationality-linked population, and may never infer an individual's
  status from anything other than their own answer.

## CONTEXT PACK SLICE (from `CONTEXT_PACK.md`)

**§2 · the pilled value (pv) shape, every quantitative claim in the pack:**

```json
{"value": "$150-175K", "pill": "Sourced", "method": "OFLC 2026 filings, 14 rows", "as_of": "2026-06"}
```
`pill` is exactly Sourced, Estimate, or Internal. `method` is required, never empty. Nothing downstream may upgrade a pill it reads from the pack.

**§3 · pack.json schema, keys and fields you read or write (NOT the full file: only the paths named above, field shapes only, `...` marks a worked-example placeholder value):**

```json
  "role": {                                        // (req)
    "slug": "acme-staff-data-engineer",
    "title": "Staff Data Engineer",                // (req)
    "level": "Staff",                              // (req)
    "company": "Acme",                             // (req)
    "org_descriptor": "50-person Series B data infrastructure company",
    "location": "SF Bay Area",
    "work_model": "Hybrid, 3 days on-site",
    "team": "Platform team of 6, one staff peer",
    "hm_names": ["..."], "recruiter_names": ["..."]
  },
  "assumptions": ["Stated defaults and user waivers, verbatim."],
  "built": "2026-08-03",                           // (req) date of last full build,
  "built_from": ["scout"],
  "caveats": ["One line per seed or import: what it does not establish."],
  "channels": {
    "mix": [{"channel": "Outbound LinkedIn", "share": 0.55,
             "basis": {"pill": "Estimate", "method": "GEM-BM 2025 outbound benchmarks"}}],
    "sequence_frame": "3-touch, day 0 / 4 / 11, channel switch on touch 3."
  },
  "comp": {
    "canonical_range": {"value": "$210-245K base", "pill": "Sourced",
                        "method": "OFLC 2026 + levels.fyi 2026 triangulation", "as_of": "2026-07"},
    "frame": {"posture": "Match market at P60", "anchor": "...",
              "equity_note": "...", "basis": "..."},
    "by_level": [
      {"level": "Senior", "base": {"value": "...", "pill": "...", "method": "..."},
       "total": {"value": "...", "pill": "...", "method": "..."}, "note": "..."}
    ],
    "positioning": "One line on where the range sits against the market spread."
  },
  "constraints": [],
  "freshness": {"market": "2026-08-03", "comp": "2026-08-03",
                "targets": "2026-08-03", "spec": "2026-08-03", "keywords": "2026-08-03"},
  "keywords": {
    "primary": ["..."], "title_synonyms": ["..."],
    "cross_industry_pools": ["..."], "skill_transfer_notes": ["..."]
  },
  "market": {
    "classification": {"value": "SCARCE", "pill": "Estimate",
                       "method": "BLS-OES 2025 baseline, 5-stage filter", "as_of": "2026-08"},
    "ratio": {"value": "1:9 engaged supply to open demand", "pill": "Estimate",
              "method": "BLS-OES vs HIRINGLAB postings", "as_of": "2026-08"},
    "funnel": {
      "baseline": {"value": "~48,200", "pill": "Sourced", "method": "BLS-OES 2025, SOC 15-1243, national", "as_of": "2026-05"},
      "stages": [
        {"name": "Meets staff bar", "pct": 0.20, "basis": "ONET skill profile filter", "pill": "Estimate"}
      ]
    },
    "demand": [{"name": "AI infra hiring wave", "read": "..."}],
    "macro": {
      "shortage_rate": {"value": "...", "pill": "Sourced", "method": "BLS-JOLTS 2026-06", "as_of": "2026-06"},
      "cost_of_vacancy": {"value": "...", "pill": "Estimate", "method": "..."}
    }
  },
  "messaging": {
    "urgency": "Why now, one line a candidate would believe.",
    "comp_angle": "How to talk about the range without apologizing for it.",
    "pain_point_angles": ["..."]
  },
  "pack_version": "1.0",
  "personas": [
    {"name": "The plateaued platform lead", "who": "...",
     "optimizes_for": "...", "message_key": "...", "risk": "..."}
  ],
  "spec": {
    "requirements": [                              // calibrated requirement ledger
      {"name": "Distributed data pipelines at production scale",
       "verdict": "must", "verified_by": "HM intake 2026-08-01"}
    ],
    "must_have_skills": ["..."], "nice_to_have": ["..."],
    "years_experience": {"value": "8+", "pill": "Estimate", "method": "recruiter-stated"},
    "education": {"value": "None required", "pill": "Internal", "method": "profile"},
    "assessment_methods": ["..."],
    "tradeoff_lock": "Depth over breadth: trade platform polish for pipeline reliability experience.",
    "seniority_ladder": "Senior -> Staff -> Senior Staff; Staff here means org-level scope."
  },
  "targets": {
    "tier1": [{"name": "...", "tier": "S", "angle": "..."}],
    "peripheral": [{"name": "...", "why": "..."}],
    "geo_sequence": ["..."],
    "triggers": [{"company": "...", "event": "...", "date": "2026-07-14",
                  "source": "WARN CA filing", "pill": "Sourced"}]
  },
  "timing": {"windows": [{"window": "...", "why": "..."}],
             "sla": {"time_to_fill": "...", "stage_turnaround": "..."}},
```

`market.classification` is exactly one of ABUNDANT, BALANCED, TIGHT, SCARCE (loosest
supply to tightest), defined ONCE here. This is the only vocabulary for market
tightness anywhere in the kit; no agent file may use a second one. Legacy 0.9.x agent
prose used a different four-point scale for the same axis; the mapping, for anyone
reading or updating that prose, is:

| Pack (1.0) | Legacy 0.9.x term |
|---|---|
| ABUNDANT | LOOSE |
| BALANCED | MODERATE |
| TIGHT | TIGHT |
| SCARCE | CRITICAL |

An agent file that still reads LOOSE/MODERATE/CRITICAL for market tightness is out of
date and should be corrected to the pack's vocabulary above.

**§3.5 · pack-research.json schema, keys you read (only atlas/hunter/shakespeare/scout/qa-gate read this file at all):**

```json
  "demand_blocs": [{"name": "...", "reqs": "...", "velocity": "...", "read": "..."}],
  "dossiers": [
    {"name": "...", "flag": "cautious|no-go|clear", "trigger": "...",
     "trigger_date": "...", "trigger_source": "...",
     "pool": {"value": "...", "pill": "...", "method": "..."}, "angle": "..."}
  ],
  "metros": [
    {"name": "Denver", "pool": {"value": "...", "pill": "Sourced", "method": "BLS-OES 2025 metro"},
     "anchors": "...", "ownership": {"value": "...", "pill": "Sourced", "method": "ACS B25003 2024"},
     "housing": "...", "tax": "...", "relo_chip": "Med-high"}
  ],
  "persona_detail": [{"name": "...", "where_found": "...", "objections": ["..."], "proof_wants": "..."}],
  "proof_points": [{"claim": "...", "source": "...", "date": "...", "url": "...", "pill": "Sourced"}],
  "quadrant": [{"name": "...", "x": 0.74, "y": 0.16, "size": 0.9, "tier": "S"}],
```

**§4 · freshness table (per pack section, not per pack):**

Relay applies the freshness table to `freshness.<section>`:

| Section | Reuse | Refresh window | Regenerate |
|---|---|---|---|
| market, targets | < 60 days | 60-90 days | 90+ days |
| comp | < 6 months (hard SLA) | - | 6 months+ |
| spec, keywords, personas, channels, messaging, timing | < 90 days | 90-135 days | 135+ days |

A sectional refresh is a scout run scoped to the stale sections only; fresh sections
pass through unchanged. Any refresh updates that section's `freshness` stamp and
`built_from`.

---
