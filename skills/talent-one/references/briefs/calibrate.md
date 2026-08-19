<!--
GENERATED FILE. Do not hand-edit.
Generator: skills/talent-one/scripts/build_briefs.py
Source fingerprint: 9543d21ad5f4
Inputs: 00_SHARED_CORE.md, 02_GROUNDING_MATRIX.md, CONTEXT_PACK.md, content-schemas/TK_07.content-schema.json
Regenerate: python3 skills/talent-one/scripts/build_briefs.py
-->

# BRIEF · A07 CALIBRATE

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

Your bound content schema: `TK_07.content-schema.json`. This brief's SCHEMA SUMMARY section below is the compact form (slot names, types, word ranges, repeat/toggle/optional structure); it replaces reading the schema JSON and the worked example-content JSON directly.

### 5.2 The content JSON shape

Value forms per slot: a **string** replaces text content; **`{"html": ...}`** fills
a multi-element wrapper slot (plain structural tags only, no style attributes);
**`{"pill", "method"}`** renders a provenance pill (§3); **`null`** deletes the
slot's block (use only for slots your agent file marks conditional, e.g. `gate.1`
with no disqualifying constraint).

Repeats: a list of row objects keyed by the schema's `row_slots`. Bars ride the row
as `"bar": 0.34` (one per row) or `"bars": [..]` in document order; a range bar
takes `[start, end]`, both 0 to 1. An empty repeat list deletes the block
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

## 7. SELF-QA BEFORE EMITTING

Before writing: run the checklist implied by §§1.5-6 above (every slot filled or sanctioned-null, one pill+method per number, pack values carried unchanged, zero em dashes/forbidden phrases, one decision per callout, constraints verbatim or absent, nothing fabricated, handoff valid). Two items nothing else in this brief states:

1. No slot still carries the shipped example's content (the Propulsion Engineer search at Onepromptman). Every value is for THIS search.
2. Repeat row counts inside their `data-count` bands, or a stated reason; empty repeats are empty lists, never one hedged row.

Content JSON written to `<run folder>/content/<NN>.content.json`; final message is the §6 summary. No HTML anywhere.

## GROUNDING MATRIX SLICE (from `02_GROUNDING_MATRIX.md`)

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

## CONTEXT PACK SLICE (from `CONTEXT_PACK.md`)

**§2 · the pilled value (pv) shape, every quantitative claim in the pack:**

```json
{"value": "$150-175K", "pill": "Sourced", "method": "OFLC 2026 filings, 14 rows", "as_of": "2026-06"}
```
`pill` is exactly Sourced, Estimate, or Internal. `method` is required, never empty. Nothing downstream may upgrade a pill it reads from the pack.

**§5 · your row in the per-artifact pack requirements table:**

- Required: role, spec.requirements, comp.canonical_range, comp.frame, market.macro, timing
- Optional but used: market.classification, constraints

A missing REQUIRED path is Class A: halt with NEED_INPUT, `kind: pack_key`. The pack is the sole source of market classification and carries exactly ONE canonical comp range (`comp.canonical_range`), which every artifact states identically; disagree from your own lookup and you keep the pack value, add your finding, raise a Caution, never fork the number.

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
  "comp": {
    "canonical_range": {"value": "$210-245K base", "pill": "Sourced",
                        "method": "OFLC 2026 + levels.fyi 2026 triangulation", "as_of": "2026-07"},
    "frame": {"posture": "Match market at P60", "anchor": "...",
              "equity_note": "...", "basis": "..."}
  },
  "constraints": [],
  "market": {
    "classification": {"value": "SCARCE", "pill": "Estimate",
                       "method": "BLS-OES 2025 baseline, 5-stage filter", "as_of": "2026-08"},
    "macro": {
      "shortage_rate": {"value": "...", "pill": "Sourced", "method": "BLS-JOLTS 2026-06", "as_of": "2026-06"},
      "cost_of_vacancy": {"value": "...", "pill": "Estimate", "method": "..."}
    }
  },
  "spec": {
    "requirements": [                              // calibrated requirement ledger
      {"name": "Distributed data pipelines at production scale",
       "verdict": "must", "verified_by": "HM intake 2026-08-01"}
    ]
  },
  "timing": {"windows": [{"window": "...", "why": "..."}],
             "sla": {"time_to_fill": "...", "stage_turnaround": "..."}},
```

`market.classification` is exactly one of ABUNDANT, BALANCED, TIGHT, SCARCE (loosest
supply to tightest), defined ONCE here. This is the only vocabulary for market
tightness anywhere in the kit; no agent file may use a second one.


## SCHEMA SUMMARY · `TK_07.content-schema.json` (template: `TK_07_HM_Calibration.dc.html`)

Format: `name (type MIN-MAX)`, word count not the full JSON or worked example prose; a slot ranged 24-24 wants 24 words, not 8 and not 60. `*` = synthetic: prose the template generator found beyond the named data-slot elements, filled exactly like any other slot, never left as the shipped example text.

### Top-level slots
- kit.mark (prose_short 4-4)
- doc.agent (prose_short 3-4)
- doc.date (prose_short 2-8)
- doc.eyebrow (prose_short 5-6)
- doc.title (label 2-3)
- role.title (label 4-4)
- role.org (prose_short 6-9)
- doc.thesis (prose_long 24-48)
- cover.note (prose_short 3-13)
- sA.title (label 5-5)
- sA.body (prose_long 29-29)
- sB.title (label 2-2)
- sB.body (prose_long 43-43)
- comp.anchor (prose_long 44-44)
- comp.premium (prose_long 33-33)
- sC.title (label 6-6)
- sC.body (prose_long 30-30)
- sD.title (label 3-3)
- sD.body (prose_long 34-34)
- sE.title (label 5-5)
- sE.body (prose_long 33-33)
- sF.title (label 2-2)
- sF.body (prose_long 36-36)
- sG.title (label 5-5)
- sG.body (prose_long 39-39)
- to.selected (prose_short 12-12)
- gate.1 (prose_long 16-46)
- footer.left (prose_short 6-7)
- footer.right (prose_short 3-6)
- doc.prose0 (prose_long ?-?)*
- doc.prose1 (prose_long ?-?)*
- doc.prose2 (prose_long ?-?)*
- doc.prose3 (prose_long ?-?)*

### Repeats
- cover.decisions [rows n=3-5]
  - decision.item (prose_short 6-6)
- market.stats [rows n=3-6]
  - stat.label (label 5-5)
  - stat.value (metric 1-1)
  - stat.detail (prose_short 13-13)
  - stat.pill (pill 1-1)
- comp.rows [rows n=3-6 bars=1(range)]
  - comp.label (label 2-4)
  - comp.n (prose_short 6-7)
  - comp.range (currency_range 1-5)
- comp.sources [rows n=3-6]
  - src.name (label 7-7)
  - src.low (currency 1-1)
  - src.mid (currency 1-1)
  - src.high (currency 1-1)
  - src.read (prose_short 6-6)
- timing.windows [rows n=2-4]
  - window.label (label 4-4)
  - window.body (prose_long 38-38)
- agenda [rows n=4-8]
  - agenda.time (count_range 1-1)
  - agenda.segment (label 3-3)
  - agenda.objective (prose_short 19-19)
- intake.questions [rows n=6-12]
  - iq.text (prose_short 23-23)
  - iq.extract (prose_short 23-23)
- requirements [rows n=4-10]
  - req.name (label 8-8)
  - req.verdict (chip 1-1)
  - req.rec (prose_short 16-16)
- tradeoffs [rows n=3]
  - to.choice (chip 3-3)
  - to.consequence (prose_short 18-18)
- sla.recruiter [rows n=3-6]
  - sla.item (prose_short 4-4)
  - sla.when (count_range 1-1)
- sla.hm [rows n=3-6]
  - hm.item (label 3-3)
  - hm.when (duration 3-3)

### Optional blocks
- `optional_1` (handoff_block=True): Handoff → all downstream artifacts Internal · optional: delete before sharing outside the search tea
