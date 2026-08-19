# CONTEXT PACK · THE PER-ROLE DECISION FILE

Version 1.0. This file defines the Context Pack, the single source of every
cross-artifact decision in a Talent One role. It supersedes `handoffs.json` as the
runtime data path between agents. `handoffs.json` remains a read-compatible audit and
migration format (see MIGRATION below); no agent reads it to build content in 1.0.

Why it exists: in 0.9.x every run re-derived shared decisions through a sequential
agent chain (calibrate then sensei then atlas, each a cold start). In 1.0 one research
pass builds the pack, then every artifact agent runs in parallel against it. Decide
once, render many.

---

## 1. FILES AND LOCATIONS

Two files, both JSON, both living in the role home:

| File | Contents | Budget | Read by |
|---|---|---|---|
| `talent-one-roles/<role_slug>/pack.json` | Every cross-artifact decision and canonical value | ≤ 4,000 tokens | every artifact agent, whole file |
| `talent-one-roles/<role_slug>/pack-research.json` | Extended findings: company dossiers, metro rows, demand blocs, persona detail, proof points | ≤ 8,000 tokens | A03, A04, A05 only |

At spawn time the orchestrator copies both into the run folder
(`runs/<YYYY-MM-DD>/pack.json`, `pack-research.json`) so every run is auditable
against the exact pack it was built from. The role-home copy is canonical; the run
copy is a snapshot and is never edited after the run.

Who writes them: the `scout` agent (a full or sectional research pass), or the
orchestrating skill (seeding from user material, importing an external deep-research
output, migrating legacy handoffs). Artifact agents NEVER write the pack.

---

## 2. THE PILLED VALUE (pv)

Every quantitative claim in the pack is a pilled-value object, never a bare number:

```json
{"value": "$150-175K", "pill": "Sourced", "method": "OFLC 2026 filings, 14 rows", "as_of": "2026-06"}
```

- `pill`: exactly `Sourced`, `Estimate`, or `Internal` (00_SHARED_CORE.md §3).
- `method`: the one-line method that renders beside the pill. A Sourced pill names
  the source and its vintage. Required, never empty.
- `as_of`: `YYYY-MM` or `YYYY-MM-DD`. Required on comp, market, and trigger values;
  optional elsewhere.
- Qualitative reads (a persona description, a positioning line) are plain strings.

Seed floor rules apply unchanged (ADAPTATIONS.md item 13d): a dated named document
is Sourced and cites name + date; a user assertion is an Estimate with method
`recruiter-stated`; Internal only for exports from the client's own system of record.
Nothing downstream may upgrade a pill it reads from the pack.

---

## 3. pack.json SCHEMA

Top-level shape. Keys marked (req) are structurally required for the pack to be
usable at all; per-artifact requirements are in §5. Omit what you do not know:
an omitted key is an honest absence and preflight halts where it is required.
Never write a placeholder, "TBD", or an empty pv to silence a halt.

```json
{
  "pack_version": "1.0",
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
  "built": "2026-08-03",                           // (req) date of last full build
  "built_from": ["scout"],                         // any of: "scout", "inputs/<file>",
                                                   // "external-deep-research",
                                                   // "legacy-handoffs", "user_stated"
  "web_calls_used": 9,                             // (req when built_from includes
                                                   // "scout") searches + fetches the
                                                   // build actually spent, self-
                                                   // reported by scout; the 12-call
                                                   // budget is audited from this by
                                                   // validate-pack and qa-gate
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
  "keywords": {
    "primary": ["..."], "title_synonyms": ["..."],
    "cross_industry_pools": ["..."], "skill_transfer_notes": ["..."]
  },
  "personas": [
    {"name": "The plateaued platform lead", "who": "...",
     "optimizes_for": "...", "message_key": "...", "risk": "..."}
  ],
  "channels": {
    "mix": [{"channel": "Outbound LinkedIn", "share": 0.55,
             "basis": {"pill": "Estimate", "method": "GEM-BM 2025 outbound benchmarks"}}],
    "sequence_frame": "3-touch, day 0 / 4 / 11, channel switch on touch 3."
  },
  "targets": {
    "tier1": [{"name": "...", "tier": "S", "angle": "..."}],
    "peripheral": [{"name": "...", "why": "..."}],
    "geo_sequence": ["..."],
    "triggers": [{"company": "...", "event": "...", "date": "2026-07-14",
                  "source": "WARN CA filing", "pill": "Sourced"}]
  },
  "messaging": {
    "urgency": "Why now, one line a candidate would believe.",
    "comp_angle": "How to talk about the range without apologizing for it.",
    "pain_point_angles": ["..."]
  },
  "timing": {"windows": [{"window": "...", "why": "..."}],
             "sla": {"time_to_fill": "...", "stage_turnaround": "..."}},
  "constraints": [],
  "caveats": ["One line per seed or import: what it does not establish."],
  "assumptions": ["Stated defaults and user waivers, verbatim."],
  "freshness": {"market": "2026-08-03", "comp": "2026-08-03",
                "targets": "2026-08-03", "spec": "2026-08-03", "keywords": "2026-08-03"}
}
```

`constraints` is copied VERBATIM from the profile by the orchestrating skill, never
written by scout, never seeded from anything else (ADAPTATIONS.md item 13g). Empty
means no eligibility gate anywhere.

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

## 3.5 pack-research.json SCHEMA

Sectioned findings for the three research-heavy artifacts. Same pv convention.

```json
{
  "pack_version": "1.0",
  "role_slug": "acme-staff-data-engineer",
  "built": "2026-08-03",
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
  "demand_blocs": [{"name": "...", "reqs": "...", "velocity": "...", "read": "..."}],
  "persona_detail": [{"name": "...", "where_found": "...", "objections": ["..."], "proof_wants": "..."}],
  "proof_points": [{"claim": "...", "source": "...", "date": "...", "url": "...", "pill": "Sourced"}],
  "quadrant": [{"name": "...", "x": 0.74, "y": 0.16, "size": 0.9, "tier": "S"}]
}
```

`quadrant` x/y are final render fractions (x = build cadence axis, y = integration
axis, already inverted for the plot); scout computes them once, atlas and the
renderer reuse them, geometry never disagrees.

---

## 4. FRESHNESS (PER SECTION, NOT PER PACK)

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

## 5. PER-ARTIFACT PACK REQUIREMENTS (PREFLIGHT KEYS)

This table replaces the 0.9.x handoff DAG. An artifact agent's preflight
(00_SHARED_CORE.md §1.5) verifies these exact paths exist in the pack it was given.
A missing required path is Class A: halt with NEED_INPUT naming the path, kind
`pack_key`. There are no inter-artifact dependencies left; all eight run in parallel.

| Artifact | Required pack paths | Optional but used |
|---|---|---|
| 07 calibrate | role, spec.requirements, comp.canonical_range, comp.frame, market.macro, timing | market.classification, constraints |
| 01 sensei | role, spec.must_have_skills, keywords.primary, keywords.title_synonyms, spec.seniority_ladder | keywords.cross_industry_pools, skill_transfer_notes |
| 03 atlas | role, market.classification, market.funnel, targets.tier1, targets.geo_sequence, comp.by_level, personas + research: dossiers, metros, quadrant | market.demand, demand_blocs, targets.peripheral |
| 02 jdbot | role, spec.requirements, spec.must_have_skills, comp.canonical_range, keywords.title_synonyms | spec.nice_to_have, constraints, spec.assessment_methods |
| 06 interview-lab | role, spec.requirements, spec.must_have_skills, timing.sla | constraints, spec.assessment_methods |
| 08 recruiter-screen | role, spec.requirements, comp.canonical_range, keywords.title_synonyms | constraints, messaging.comp_angle |
| 04 hunter | role, keywords, market.funnel, targets.tier1, channels, personas + research: metros, persona_detail | targets.peripheral, market.classification |
| 05 shakespeare | role, personas, channels, messaging + research: proof_points | targets.triggers, comp.canonical_range |

Consistency contract, unchanged in spirit: the pack is the sole source of market
classification and carries exactly ONE canonical comp range
(`comp.canonical_range`), which every artifact states identically. An agent that
disagrees with the pack from its own artifact-specific lookup keeps the pack value,
adds its finding, and raises a Caution callout; it never silently overrides
(00_SHARED_CORE.md §2.3).

---

## 6. SEEDING INTO THE PACK

ADAPTATIONS.md item 13 retargets from handoffs.json to the pack; every floor rule
survives:

- A seed fills only the pack paths its source actually states; unstated paths are
  omitted, and a downstream halt on an omitted path is the system working.
- Pills at the seed floor (item 13d), never upgraded downstream.
- `market.classification`, `market.funnel`, comp guidance, and `personas` seed only
  from a dated market document, a cached pack or Atlas run, or an external
  deep-research import with named dated sources; NEVER from a bare assertion.
- `constraints` never seeds: profile only, verbatim.
- Only skills write seeds. Record each seed's source in `built_from` and its limit
  in `caveats`; agents copy relevant caveats into their content and the rendered
  handoff assumptions.

## 7. MIGRATION (LEGACY handoffs.json -> pack)

Relay finds legacy handoffs for the same role (both folder layouts) and offers a
migration import. Mapping, applied by the orchestrating skill with pills preserved:

calibrate: `requirements[]` -> spec.requirements · `comp_frame` -> comp.frame (+
comp.canonical_range when it states one) · `timing_windows[]` -> timing.windows ·
`tradeoff_lock` -> spec.tradeoff_lock · `sla` -> timing.sla · `constraints[]` ->
DISCARD (re-copy from profile).
sensei: `primary_keywords[]` -> keywords.primary · `title_synonyms[]` ->
keywords.title_synonyms · `cross_industry_pools[]`, `skill_transfer_notes[]` ->
keywords.* · `seniority_ladder` -> spec.seniority_ladder · `must_have_skills[]` ->
spec.must_have_skills.
atlas: `market` -> market.classification · `funnel` -> market.funnel ·
`comp_guidance` -> comp.frame/by_level · `tier1_targets[]` -> targets.tier1 ·
`peripheral[]` -> targets.peripheral · `geo_sequence[]` -> targets.geo_sequence ·
`personas[]` -> personas · `market_urgency` -> messaging.urgency · `comp_messaging`
-> messaging.comp_angle · `pain_point_angles[]` -> messaging.pain_point_angles.
jdbot: `must_have_skills[]`, `nice_to_have[]`, `years_experience`, `education`,
`assessment_methods[]` -> spec.* · `posted_range` -> comp.canonical_range (flag a
conflict if both exist and disagree; never silently pick one).
hunter: `channel_mix[]` -> channels.mix · `personas[]` -> merge into personas ·
`target_companies[]` -> targets.tier1 merge. `search_strings[]` and `pipeline_math`
stay artifact content; they do not enter the pack.

Each migrated section keeps the ORIGINAL `generated` date as its `freshness` stamp,
so the §4 table applies honestly. `built_from` gains `"legacy-handoffs"`.

## 8. COMPAT: handoffs.json IN 1.0 RUNS

After rendering, the renderer writes a compat `handoffs.json` into the run folder,
derived from each artifact's content handoff block (see 00_SHARED_CORE.md §6). It
exists for auditability, legacy relay reads, and qa-gate cross-checks. It is
derived output, never an input, and never hand-edited.
