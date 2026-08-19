<!--
GENERATED FILE. Do not hand-edit.
Generator: skills/talent-one/scripts/build_briefs.py
Source fingerprint: 939a3a54a03e
Inputs: 00_SHARED_CORE.md, 02_GROUNDING_MATRIX.md, CONTEXT_PACK.md
Regenerate: python3 skills/talent-one/scripts/build_briefs.py
-->

# BRIEF · RELAY (planning broker)

relay has no shared-core slice (it never writes provenance, content, or a handoff, and never halts via NEED_INPUT) and no grounding-matrix slice (it does no research). Its whole job runs off CONTEXT_PACK.md's structural tables, reproduced here in full since relay computes a UNION across whichever artifacts were requested and so needs every row, not one.

## CONTEXT PACK: FULL §5 REQUIREMENTS TABLE

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

Union the requested artifacts' rows: that union is scout's scope when a build or sectional refresh is needed. Note which artifacts also need `pack-research.json` (03, 04, 05).

## CONTEXT PACK: §4 FRESHNESS TABLE

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

## CONTEXT PACK: §1 FILES AND LOCATIONS

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

## CONTEXT PACK: §6 SEEDING RULES (for the seed-candidate step)

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

## CONTEXT PACK: market.classification vocabulary

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

## PHASE STRUCTURE (fixed, from relay.md itself, reproduced for quick reference)

Phase 1: Context Pack build/refresh/import (scout, or skill-seeded). Phase 2: every requested artifact agent, all parallel, each fed the pack files. Phase 3: deterministic render (`scripts/render.py`), then qa-gate when 2+ artifacts were built. No inter-artifact DAG: the pack carries every cross-artifact decision.
