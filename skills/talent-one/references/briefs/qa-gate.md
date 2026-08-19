<!--
GENERATED FILE. Do not hand-edit.
Generator: skills/talent-one/scripts/build_briefs.py
Source fingerprint: 939a3a54a03e
Inputs: 00_SHARED_CORE.md, 02_GROUNDING_MATRIX.md, CONTEXT_PACK.md
Regenerate: python3 skills/talent-one/scripts/build_briefs.py
-->

# BRIEF · A09 QA GATE

Precompiled slice of this kit's four reference files, scoped to what this agent needs. Read this file only; it replaces reading 00_SHARED_CORE.md, CONTEXT_PACK.md, 02_GROUNDING_MATRIX.md, and this agent's content-schema + example-content pair in full.

## SHARED CORE SLICE (from `00_SHARED_CORE.md`)

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

**Constraints (eligibility gates)**

Some searches carry hard eligibility requirements: work authorization, visa
sponsorship, security clearance, professional licensure, onsite or hybrid presence,
a background or credit check, or a regulatory eligibility rule specific to the
industry. The list below is illustrative, not exhaustive: the mechanism takes whatever
the recruiter writes.

These are **recruiter-configured, never assumed**. Read `config.constraints[]`. Each
entry is:

```yaml
- label: Work authorization
  requirement: Must be authorized to work in the US without current or future sponsorship.
  gate_stage: screen          # screen | application | offer
  disqualifying: true         # true = a No ends the process
```

Rules:

1. If `config.constraints` is empty or absent, **the pack ships no gate at all**. Do
   not invent one, do not add a generic work-authorization line, do not hint that one
   might exist.
3. A constraint with `disqualifying: true` renders as a **Gate** callout (jeok accent).
   Non-disqualifying constraints render as ordinary body content.
5. Never state or estimate the size of a protected-class or nationality-linked
   population. Eligibility is a per-candidate question asked at
   `gate_stage`, not a demographic model.

---

## 5. CONTENT CONTRACT (SUPERSEDES THE 0.9.x TEMPLATE FILL CONTRACT)

**You never emit HTML. You emit one content JSON file** conforming to your bound
content schema, and `scripts/render.py` fills your template deterministically.
Geometry sync, pill spans, design-system inlining, and branding are the script's
job. Yours is judgment: what the numbers are, what the reads say, what gets cut.

### 5.1 Your bound content schema

Each agent is bound to exactly one schema, generated from its template:

A09 QA GATE (you): no bound schema of your own. You audit every other agent's content JSON against ITS schema; the AUDIT CONTRACT rules below (§5.2-5.4) are the shape common to all eight, not any one schema.

### 5.2 The content JSON shape

Value forms per slot: a **string** replaces text content; **`{"html": ...}`** fills
a multi-element wrapper slot (plain structural tags only, no style attributes);
**`{"pill", "method"}`** renders a provenance pill (§3); **`null`** deletes the
slot's block (use only for slots your agent file marks conditional, e.g. `gate.1`
with no disqualifying constraint).

Repeats: a list of row objects keyed by the schema's `row_slots`. Bars ride the row
as `"bar": 0.34` (one per row) or `"bars": [..]` in document order; a range bar
takes `[start, end]`, both 0 to 1. A repeat with `row_variants` in the schema has
distinct card types matched BY POSITION: give each position the keys its variant
lists. A `grid` repeat takes `{"columns", "rows": [{"label", "cells"}]}` with cell
vocabulary exactly `primary | secondary | touch | none | gap`. A `points` repeat
takes `{"label", "x", "y"}` fractions 0 to 1 (already inverted for the plot; take
them from the pack's `quadrant` research where present) plus optional `size` px and
`accent: true` for the client-company star. An empty repeat list deletes the block
and its heading: that is the honest empty state, never hedging prose. `data-count`
in the schema is guidance: respect it unless the data genuinely demands otherwise.

Omit `"optionals"` entries you have no data for: the block is deleted. Toggles
(TK_03 only) choose which sections ship visible; never fake them elsewhere.

Synthetic prose slots: some schema entries are marked `"synthetic": true`. These
are prose sites the template carries without a `data-slot` attribute (a "why it
wins" line, a card aside); the renderer fills them by structural path. Fill every
schema-listed synthetic slot like any other slot, at the example's length and in
the search's own domain language. A synthetic slot you omit renders BLANK, never
the template's example prose; leaving one out is a visible hole in the artifact,
so omission is never a shortcut.

### 5.3 Hard rules

1. **Structure is the schema.** Every slot in the schema gets a value (or a
   sanctioned null); no keys the schema does not name; no HTML beyond wrapper-slot
   fragments.
2. **Provenance.** Section 3, applied to every number, as pill objects.
3. **Density budget per artifact:** the example content IS the budget: match its
   per-slot lengths and its callout discipline (at most 80 words per prose block).
4. **One decision per callout.** Insight = a repeatable read the recruiter can say
   out loud in a hiring-manager meeting. Caution = a known failure mode plus its
   countermeasure. Gate = binary and legal, verbatim from constraints.
5. **Include the handoff block** (section 6) in every content JSON.
6. **Write the file, return the summary.** Write content JSON to
   `<run folder>/content/<NN>.content.json`; your final message is the §6 summary,
   never the JSON body.

### 5.4 Reskinning (orchestrator-owned)

`data-mode` and brand token overrides come from the profile's branding block and are
applied by the renderer (`--mode`, `--brand`). Agents never carry branding.

---

## 6. HANDOFF IN 1.0: AUDIT TRAIL, NOT DATA PATH

The Context Pack is the runtime data path between agents. The handoff contract
survives as the audit vocabulary: your content JSON carries a `handoff` object, the
renderer fills the rendered handoff block and derives the compat `handoffs.json`.

In your content JSON:

```json
"handoff": {"keys": { ...exactly the Part 3.5 key names for your artifact... },
            "blocked": "Nothing",
            "assumptions": "carried caveats and degraded-proceed notes, or omit"}
```

Keep `keys` under 350 tokens. The key names are the API defined in
`02_GROUNDING_MATRIX.md` Part 3.5, not yours to rename: qa-gate audits against
them, and legacy runs migrate through them. The renderer derives
`handoff.produces` from your key order and the consumers line from the routing
table, so a produces mismatch is now structurally impossible; `blocked` is a real
blocker or the single word `Nothing`; `assumptions` carries pack caveats you
inherited (§1.5) and degraded-proceed costs, verbatim, or is omitted entirely.

**Your final message to the orchestrator** is: the content JSON path, your handoff
`keys` block, every Estimate-pilled figure needing human review, and any Caution
you raised. Never the full content JSON body.

---

## 7. SELF-QA BEFORE EMITTING

Run this list. Geometry, pill styling, and structure are the renderer's problem
now; what remains is yours, and A09 checks it independently.

**Content integrity**

1. Every schema slot has a value; nulls only where your agent file sanctions them.
2. No slot still carries the shipped example's content (the Propulsion Engineer
   search at Onepromptman). Every value is for THIS search.
3. Every number carries exactly one pill object with a one-line method; every
   Sourced pill's method names a source and a date.
4. Every value the pack states is carried through unchanged: same figure, same
   pill, no forks, no upgrades. The canonical comp range appears exactly as
   `comp.canonical_range` states it.
5. Zero em dashes. Zero forbidden phrases. Lengths match the example content.
6. Each callout is one decision, and the right flavour of the three.
7. Constraints, if any, are verbatim from the profile via the pack; if
   `constraints` is empty, your content contains no eligibility gate.
8. Nothing fabricated. Nothing sourced to a place you did not actually read.
9. Repeat row counts inside their `data-count` bands, or a stated reason; empty
   repeats are empty lists, never one hedged row.

**Handoff integrity**

10. `handoff.keys` valid, under 350 tokens, keyed exactly per Part 3.5.
11. `blocked` says `Nothing` or names a real blocker; inherited caveats sit in
    `assumptions` verbatim.

**Output**

12. Content JSON written to `<run folder>/content/<NN>.content.json`; final message
    is the §6 summary. No HTML anywhere.

## GROUNDING MATRIX SLICE (from `02_GROUNDING_MATRIX.md`)

### A09 QA GATE → no template

Reads everything, plus this file. Additional audits beyond the shared-core self-QA list:

1. **Provenance-to-source mapping.** Every Sourced pill must trace to a registry source
   at or above the Part 2 precedence row for its data type. A comp figure pilled to an
   aggregator while a `CSR` band exists is a FAIL.
2. HOUSE vs ORACLE labeling present in pipeline math.
3. `ATS`-derived names cross-checked against the `ORG` roster before printing.
4. Drift log present in ATLAS when funnel values changed.
5. No candidate personal data anywhere in outreach artifacts.
6. Handoff schema conformance against Part 3.5 below, both JSON keys and the rendered
   `handoff.produces` slot.

---

**Part 1 · source registry, filtered to codenames above:**
- `ATS`: Applicant tracking system · T0 · Read-only scopes: jobs, postings, offers, scorecards, users; candidate objects only for rediscovery queries
- `CSR`: **Comp System of Record**, the approved internal band · T0 · Band export to `kb/internal/comp/bands.csv`, keyed by a role-family crosswalk ID
- `ORG`: Org / headcount system · T0 · Read: org units, reporting lines, team rosters

**Part 2 · source-of-truth precedence:**
When two sources answer the same question, the higher row wins. Lower rows may
triangulate or raise a Caution callout, never silently override.

| Data type | Precedence order |
|---|---|
| Comp band / posted range | `CSR` approved band > `CSV` percentile (via crosswalk) > `ATS` accepted-offer actuals > `AGG` (triangulation only) |
| Titles and synonyms | `ATS` historical postings > `WIKI` internal lists > SENSEI web extension |
| Interview process, rubrics, interviewer names | `WIKI` verbatim > `ATS` scorecard config > never web, never invented |
| Funnel and outreach rates | House actuals from `ATS` (when n ≥ 30 for the role family) > `OR` benchmarks > web claims |
| Occupation counts, demographics, homeownership, migration | `OR` (government series) > web estimates, Estimate-pilled |
| Trigger events | `TRG` dated primary (statutory filing, newsroom, named outlet) > aggregator mention > undated rumor (unusable) |
| Company proof points | Company newsroom or regulatory filing > trade press > never memory |
| Voice and structure | `BR` + `HX` exemplar of the same artifact type > model default |

---

**Part 3.5 · consolidated handoff schema, every producer (you audit conformance across all of them):**
| Producer | Exact keys in `handoff` |
|---|---|
| A07 CALIBRATE | `requirements[]` (each `{name, verdict, verified_by}`) · `comp_frame` · `timing_windows[]` · `tradeoff_lock` · `constraints[]` · `sla` |
| A01 SENSEI | `primary_keywords[]` · `title_synonyms[]` · `cross_industry_pools[]` · `skill_transfer_notes[]` · `seniority_ladder` · `must_have_skills[]` |
| A03 ATLAS | `market` · `funnel` · `comp_guidance` · `tier1_targets[]` · `peripheral[]` · `geo_sequence[]` · `personas[]` · `market_urgency` · `comp_messaging` · `pain_point_angles[]` · `cross_industry_pools[]` · `skill_transfer_notes[]` |
| A02 JD-BOT | `must_have_skills[]` · `nice_to_have[]` · `years_experience` · `education` · `posted_range` · `assessment_methods[]` |
| A04 HUNTER | `personas[]` · `search_strings[]` · `channel_mix[]` · `pipeline_math` · `target_companies[]` |
| A06 INTERVIEW LAB | `stages[]` · `competency_coverage` · `deal_breakers[]` · `debrief_protocol` |
| A08 RECRUITER SCREEN | `grades` · `motivators_verbatim[]` · `flags[]` · `recommendation` |
| A05 SHAKESPEARE | `sequence[]` · `channels[]` · `ab_variants[]` · `banned_phrases_checked` |
| A09 QA GATE | `verdict` · `findings[]` (each `{artifact, agent, check, severity, evidence, required_fix}`) |

**`assumptions` is a sanctioned extra key, not a producer-specific one.** Any producer
may add `assumptions` to its JSON `handoff` object when `00_SHARED_CORE.md` §6.5's
degraded-proceed rule or `ADAPTATIONS.md` item 13's seeding rule applies. It is exempt
from the `handoff.produces` match: never list it in `handoff.produces`, and A09 does
not count it as a schema mismatch. Where the bound template carries a
`handoff.assumptions` slot, render the same text there; where it does not (TK_03,
TK_04, TK_05), the JSON key alone carries it. Absent, omit the key entirely rather
than emitting it empty.

**Relay note (historical).** The 0.9.x SENSEI-through-ATLAS relay for
`cross_industry_pools` and `skill_transfer_notes` no longer exists at runtime: both
fields live in the pack (`keywords.*`) and every agent reads them there. Atlas and
Sensei still carry them in their audit keys unchanged.

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

**§5 · required pack paths per artifact (you audit fidelity across every artifact, not just one; optional-but-used column omitted, see the row's own agent brief for that):**

- 07 calibrate: role, spec.requirements, comp.canonical_range, comp.frame, market.macro, timing
- 01 sensei: role, spec.must_have_skills, keywords.primary, keywords.title_synonyms, spec.seniority_ladder
- 03 atlas: role, market.classification, market.funnel, targets.tier1, targets.geo_sequence, comp.by_level, personas + research: dossiers, metros, quadrant
- 02 jdbot: role, spec.requirements, spec.must_have_skills, comp.canonical_range, keywords.title_synonyms
- 06 interview-lab: role, spec.requirements, spec.must_have_skills, timing.sla
- 08 recruiter-screen: role, spec.requirements, comp.canonical_range, keywords.title_synonyms
- 04 hunter: role, keywords, market.funnel, targets.tier1, channels, personas + research: metros, persona_detail
- 05 shakespeare: role, personas, channels, messaging + research: proof_points

**§3 · pack.json schema, keys and fields you read or write (NOT the full file: only the paths named above, field shapes only, `...` marks a worked-example placeholder value):**

```json
  "role": {
    "company": "Acme"                             // (req),
    "level": "Staff"                              // (req),
    "title": "Staff Data Engineer"                // (req)
  },
  "built_from": ["scout"],
  "caveats": ["One line per seed or import: what it does not establish."],
  "comp": {
    "canonical_range": {"value": "$210-245K base", "pill": "Sourced",
                        "method": "OFLC 2026 + levels.fyi 2026 triangulation", "as_of": "2026-07"}
  },
  "constraints": [],
  "keywords": {
    "primary": ["..."], "title_synonyms": ["..."],
    "cross_industry_pools": ["..."], "skill_transfer_notes": ["..."]
  },
  "market": {
    "classification": {"value": "SCARCE", "pill": "Estimate",
                       "method": "BLS-OES 2025 baseline, 5-stage filter", "as_of": "2026-08"}
  },
  "messaging": {
    "comp_angle": "How to talk about the range without apologizing for it.",
    "urgency": "Why now, one line a candidate would believe."
  },
  "personas": [
    {"name": "The plateaued platform lead", "who": "...",
     "optimizes_for": "...", "message_key": "...", "risk": "..."}
  ],
  "spec": {
    "must_have_skills": ["..."],
    "requirements": [                              // calibrated requirement ledger
      {"name": "Distributed data pipelines at production scale",
       "verdict": "must", "verified_by": "HM intake 2026-08-01"}
    ]
  },
```

`market.classification` is exactly one of ABUNDANT, BALANCED, TIGHT, SCARCE (loosest
supply to tightest), defined ONCE here. This is the only vocabulary for market
tightness anywhere in the kit; no agent file may use a second one.

**§3.5 · pack-research.json schema, keys you read (only atlas/hunter/shakespeare/scout/qa-gate read this file at all):**

```json
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
  "proof_points": [{"claim": "...", "source": "...", "date": "...", "url": "...", "pill": "Sourced"}],
  "quadrant": [{"name": "...", "x": 0.74, "y": 0.16, "size": 0.9, "tier": "S"}],
```
