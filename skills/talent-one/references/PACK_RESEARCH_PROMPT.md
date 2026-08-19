# External pack building: the paste-ready deep-research prompt

Copy everything between the START and END markers into a Claude deep-research (or
equivalent) session, fill the ROLE FACTS block, and attach any material you hold
(JD, intake notes, comp data). Save the returned JSON as
`talent-one-roles/<role_slug>/inputs/pack-research-<YYYY-MM-DD>.json`. On the next
run, relay detects it, the skill validates it (`render.py validate-pack`), splits
it into `pack.json` + `pack-research.json`, and scout does not need to run.

The output's provenance survives import: dated named sources stay Sourced, derived
figures stay Estimates. A validated external file with named dated sources meets
the bar for market, funnel, comp, and personas (ADAPTATIONS item 22); nothing in it
may claim Internal unless it came from an attached export of your own system of
record.

---- START OF PROMPT (copy from here) ----

You are building a Context Pack: the complete research layer for one hiring search,
consumed by a downstream document pipeline. Your output is ONE JSON code block and
nothing else, top-level keys `"pack"` and `"research"`, exactly in the shapes below.
Research deeply before writing: government labor data, dated filings, named
industry sources. This pack will be quoted verbatim in recruiter-facing documents,
so every claim must be defensible.

## ROLE FACTS (filled by the requester)

- Role title:
- Level:
- Company (+ one-line descriptor):
- Location / work model:
- Team context:
- Comp posture or any known band:
- Anything already decided (attach JD, intake notes, comp data if held):

## HARD RULES

1. **Every quantitative claim is a pilled-value object**:
   `{"value": "...", "pill": "Sourced|Estimate", "method": "<source + vintage or
   calculation>", "as_of": "YYYY-MM"}`. Sourced means you read a verifiable dated
   source and the method names it ("BLS OES 2025, SOC 15-1243"; "DOL OFLC 2026
   filings"; "WARN CA notice 2026-07-14"). Estimate means you derived it and the
   method says how. Never use the pill Internal. A figure you cannot pill honestly
   is a figure you omit.
2. **Omit what you cannot ground.** Missing keys are honest; empty strings, "TBD",
   "N/A", or invented values poison the pipeline and are the worst failure mode.
3. **One canonical comp range.** `pack.comp.canonical_range` is THE number the
   whole kit quotes. Triangulate: employer wage filings (DOL OFLC) beat salary
   aggregators; two independent aggregators that agree make an Estimate; one alone
   is not evidence.
4. **The funnel starts Sourced, derives Estimates.** Baseline = a government
   occupation count (BLS OES, national or metro). Each of up to five stages below
   it is a named filter with `pct` (0 to 1, fraction of the PREVIOUS stage
   remaining) and a stated basis. Classification is exactly one of ABUNDANT,
   BALANCED, TIGHT, SCARCE.
5. **Triggers are dated or dead.** A layoff, funding, RTO, or leadership event
   enters only with a date and a named source; statutory filings (WARN) outrank
   tracker entries; an undated rumor is unusable.
6. **Do NOT include eligibility constraints** (work authorization, clearance,
   licensure). Those are configured by the recruiter elsewhere; nothing you write
   may hint at one.
7. **No em dashes anywhere.** Use commas, colons, or parentheses. Keep every prose
   value under 30 words. Total budget: "pack" under roughly 3,000 words of JSON,
   "research" under roughly 6,000.
8. **Personas and messaging are grounded in the research**, not generic recruiter
   copy: each persona names who they are, what they optimize for, the one message
   that lands, and the risk to screen for.

## OUTPUT SHAPE

```json
{
  "pack": {
    "pack_version": "1.0",
    "role": {"slug": "<company>-<role>", "title": "", "level": "", "company": "",
             "org_descriptor": "", "location": "", "work_model": "", "team": ""},
    "built": "YYYY-MM-DD",
    "built_from": ["external-deep-research"],
    "spec": {
      "requirements": [{"name": "", "verdict": "must|nice", "verified_by": ""}],
      "must_have_skills": [], "nice_to_have": [],
      "years_experience": {"value": "", "pill": "", "method": ""},
      "education": {"value": "", "pill": "", "method": ""},
      "seniority_ladder": "", "tradeoff_lock": ""
    },
    "market": {
      "classification": {"value": "SCARCE", "pill": "Estimate", "method": "", "as_of": ""},
      "ratio": {"value": "", "pill": "", "method": "", "as_of": ""},
      "funnel": {
        "baseline": {"value": "", "pill": "Sourced", "method": "", "as_of": ""},
        "stages": [{"name": "", "pct": 0.0, "basis": "", "pill": "Estimate"}]
      },
      "demand": [{"name": "", "read": ""}],
      "macro": {"shortage_rate": {}, "cost_of_vacancy": {}}
    },
    "comp": {
      "canonical_range": {"value": "", "pill": "", "method": "", "as_of": ""},
      "frame": {"posture": "", "anchor": "", "equity_note": "", "basis": ""},
      "by_level": [{"level": "", "base": {}, "total": {}, "note": ""}],
      "positioning": ""
    },
    "keywords": {"primary": [], "title_synonyms": [],
                 "cross_industry_pools": [], "skill_transfer_notes": []},
    "personas": [{"name": "", "who": "", "optimizes_for": "", "message_key": "", "risk": ""}],
    "channels": {"mix": [{"channel": "", "share": 0.0,
                          "basis": {"pill": "Estimate", "method": ""}}],
                 "sequence_frame": ""},
    "targets": {
      "tier1": [{"name": "", "tier": "S|A|B|C", "angle": ""}],
      "peripheral": [{"name": "", "why": ""}],
      "geo_sequence": [],
      "triggers": [{"company": "", "event": "", "date": "YYYY-MM-DD",
                    "source": "", "pill": "Sourced"}]
    },
    "messaging": {"urgency": "", "comp_angle": "", "pain_point_angles": []},
    "timing": {"windows": [{"window": "", "why": ""}], "sla": {}},
    "caveats": ["one line per thing this research could not establish"],
    "freshness": {"market": "YYYY-MM-DD", "comp": "YYYY-MM-DD", "targets": "YYYY-MM-DD",
                  "spec": "YYYY-MM-DD", "keywords": "YYYY-MM-DD"}
  },
  "research": {
    "pack_version": "1.0", "role_slug": "", "built": "YYYY-MM-DD",
    "dossiers": [{"name": "", "flag": "clear|cautious", "trigger": "",
                  "trigger_date": "", "trigger_source": "",
                  "pool": {"value": "", "pill": "", "method": ""}, "angle": ""}],
    "metros": [{"name": "", "pool": {}, "anchors": "",
                "ownership": {}, "housing": "", "tax": "",
                "relo_chip": "High|Med-high|Med|Med-low|Low"}],
    "demand_blocs": [{"name": "", "reqs": "", "velocity": "", "read": ""}],
    "persona_detail": [{"name": "", "where_found": "", "objections": [], "proof_wants": ""}],
    "proof_points": [{"claim": "", "source": "", "date": "", "url": "", "pill": "Sourced"}],
    "quadrant": [{"name": "", "x": 0.0, "y": 0.0, "size": 13, "tier": "S|A|B|C"}]
  }
}
```

Quadrant: x = build cadence (0 slow to 1 fast), y = hardware/software integration
depth rendered top-down (0 = deepest, near the top of the plot), both plot-ready
fractions; include the hiring company itself with `"accent": true` and `"size": 15`.
Fill 5 to 9 dossiers, 4 to 7 metros, 3 to 5 personas, 5 to 7 tier1 targets. Return
ONLY the JSON code block.

---- END OF PROMPT ----
