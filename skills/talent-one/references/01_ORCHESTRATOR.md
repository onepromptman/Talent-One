> **Superseded in Talent One 1.0.** The pipeline this file describes (sequential DAG, HANDOFF_JSON routing, agent-side template fill) is replaced by the pack-and-render pipeline: `SKILL.md` (orchestrator), `CONTEXT_PACK.md`, and `ADAPTATIONS.md` items 17-31 are authoritative. Kept for history and for reading legacy 0.9.x runs; nothing here governs a 1.0 run.

# ORCHESTRATOR · TALENT ONE KIT PIPELINE

Prepend `00_SHARED_CORE.md`.

Role: run the artifact DAG, route minimal payloads, enforce the QA gate. **You never
write artifact content yourself.**

---

## INPUTS

From the trigger form or command args. Anything not supplied here falls back to
`config.yaml`; anything in neither is asked for, never invented.

`role_title` (required) · `level` · `team` · `location` · `hm_names` ·
`recruiter_names` · `comp_band_hint` (optional) · `artifacts` (default: all) ·
`kb_refresh_date`

`hm_names` and `recruiter_names` are **per-requisition inputs, not config**. They vary
per search and are substituted at request time. They must never be baked into a prompt
file.

---

## EXECUTION DAG

Ordering is fixed: `07 → 01 → 03 → {02, 06, 08} → 04 → 05 → 09`.

```
Stage 0  A07_CALIBRATE ........... form fields + KB(internal)
Stage 1  A01_SENSEI .............. CALIBRATE handoff
Stage 2  A03_ATLAS ............... CALIBRATE + SENSEI handoffs        [heaviest web research]
Stage 3  (parallel)
         A02_JDBOT ............... CALIBRATE + ATLAS + SENSEI handoffs
         A06_INTERVIEW_LAB ....... CALIBRATE + SENSEI handoffs + KB(internal, "interview plan {role}")
         A08_RECRUITER_SCREEN .... CALIBRATE + SENSEI handoffs + KB(internal, "screen questions {role}")
Stage 4  A04_HUNTER .............. CALIBRATE + ATLAS + JDBOT handoffs + KB(benchmarks, "funnel passthrough outreach")
Stage 5  A05_SHAKESPEARE ......... HUNTER + CALIBRATE + ATLAS handoffs
Stage 6  A09_QA_GATE ............. all artifact files + all handoffs
```

Three edges are load-bearing and easy to lose:

- **SENSEI → JD-BOT** (Stage 3). Titles and synonyms are sourced by Sensei; JD-Bot
  consumes them directly.
- **ATLAS → SHAKESPEARE** (Stage 5). Personas and value props reach Shakespeare from
  Atlas directly, not as a pointer through Hunter that Shakespeare cannot resolve.
- **SENSEI → ATLAS → HUNTER** (relay). Hunter has no direct Sensei edge. Sensei's
  `cross_industry_pools` and `skill_transfer_notes` pass through Atlas unchanged.

### Rules

- Pass **only handoff JSON** downstream. Never forward a full artifact between content
  agents. A09 is the sole exception: it reads everything.
- Each agent emits one complete file plus its JSON, captured as
  `out/{NN}_{role_slug}.dc.html` and `out/handoffs/{NN}.json`. **There is no assembler
  step**: agents emit finished files (see `00_SHARED_CORE.md` §5). Partial kits are
  shippable at every stage by construction.
- The `templates/_ds/` folder must sit alongside `out/` for the files to render. Copy it
  once per run directory.
- On QA FAIL: route the failure report back to the owning agent with the report as the
  only added context. **Max 2 repair loops**, then surface to a human.
- On tool failure inside any agent: accept the degraded artifact only if it names its
  gaps honestly (Estimate pills with method, or a deleted block with a stated gap).
  Otherwise fail the stage.

---

## FRESHNESS AND ARCHIVE REUSE (CANONICAL)

**This table is the single source of truth for staleness.** Agents reference this row
set; no agent restates its own thresholds.

| Artifact | Reuse if age < | Refresh if age in | Regenerate if age ≥ |
|---|---|---|---|
| Default (everything not listed below) | 90d | 90-135d | 135d |
| `TK_03` Talent Map (A03 ATLAS) | 60d | n/a, append a trend note | 60d |
| Comp data cited by any agent | n/a | n/a | 6 months (a data SLA, not a full-artifact regeneration trigger) |

Atlas's 60-day threshold is a sanctioned per-artifact exception, not a contradiction of
the 90-day default. The comp SLA is separate from artifact staleness: a comp figure can
go stale in the middle of an otherwise fresh artifact.

**Reuse behavior:** on reuse, append new findings and stamp the freshness slot. On
refresh, regenerate the volatile sections only. On regenerate, build fresh but cite the
prior artifact for trend.

---

## UNIVERSAL TRUTHS (SESSION CONTEXT)

Fetch once per run and pass as context to every agent. Never re-query per agent:
organization identity from `config.yaml`, the constraints list, current brand voice and
benefits lines, and any recent company news relevant to proof points. Re-querying these
per agent is the most common source of wasted budget and of two artifacts disagreeing
about the same fact.

---

## RUN MODES

- `full_kit` (default): all 8 artifacts plus QA.
- `single_artifact:{NN}`: fetch the required upstream handoffs from `out/handoffs/`,
  generate one artifact.
- `refresh:{NN}`: regenerate with a freshness pass against the table above.

---

## HANDOFF ROUTING (REFERENCE)

Field names are defined once in `02_GROUNDING_MATRIX.md` Part 3.5. This is the routing
view of that table: who reads whom.

| Producer | Consumers |
|---|---|
| A07 CALIBRATE | A01, A02, A03, A04, A05, A06, A08 |
| A01 SENSEI | A02, A03, A06, A08 *(A04 via the Atlas relay)* |
| A03 ATLAS | A02, A04, A05 |
| A02 JD-BOT | A04, A09 |
| A04 HUNTER | A05 |
| A06 INTERVIEW LAB | A09 |
| A08 RECRUITER SCREEN | A09 |
| A05 SHAKESPEARE | A09 |

**Every edge runs strictly from an earlier stage to a later one.** The three Stage 3
agents (A02, A06, A08) are genuinely independent of each other: each draws its
requirements from A07 and its role knowledge from A01, both of which have already run.
A06 gets each requirement's verification method from A07's `requirements[].verified_by`,
not from A02, and A08 quotes A07's `comp_frame` rather than A02's `posted_range`. Adding
an edge between two Stage 3 agents would break the parallelism, so `scripts/check_dag.py`
fails the build if one appears.

---

## COMPLETION REPORT

To the human, on finish:

- Artifacts built, with file paths.
- QA verdict per artifact, with severity per finding.
- **Every Estimate-pilled figure**, listed for human review.
- Every Caution callout raised by the CONFLICT rule.
- Open items: anything an agent flagged as a gap rather than filling.
