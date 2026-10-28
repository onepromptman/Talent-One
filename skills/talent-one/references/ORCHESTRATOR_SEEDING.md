# Orchestrator: seeding and importing (write it before you spawn)

Loaded on demand by the `talent-one` skill, section 2.7, when relay proposes seeds or `inputs/` holds an external deep-research file.

Seeds now write INTO the pack (`references/CONTEXT_PACK.md` §6; ADAPTATIONS item 13
retargeted). For each seed the user accepts, read the source document yourself and
write the pack paths it actually states, with provenance at the seed floor: a dated
named document is Sourced citing name and date; a user assertion is an Estimate with
method `recruiter-stated`; `market.classification`, funnel, comp guidance, and
personas never seed from an assertion; `constraints` never seeds, it copies verbatim
from the profile (you do this copy on every pack build). Record each seed in
`built_from` and its limit in `caveats`. Omit what the source does not state: a
downstream halt on an omitted path is the system working.

An external deep-research file (built with `references/PACK_RESEARCH_PROMPT.md`) in
`inputs/` imports the same way: validate with `render.py validate-pack`, fix or
bounce HIGH findings back to the user, install as `pack.json` +
`pack-research.json` with its provenance intact, add `external-deep-research` to
`built_from`. Show the user one line per seeded or imported section: what landed,
from what, and what it does not establish.
