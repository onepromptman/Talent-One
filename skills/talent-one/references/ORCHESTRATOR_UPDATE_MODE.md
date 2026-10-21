# Orchestrator: update mode (warm role)

Loaded on demand by the `talent-one` skill, section 5, when the user asks to change or refresh an existing artifact for a role with cached `content/`.

When the user asks to change or refresh an existing artifact for a role that has
`content/` cached: no full run. (a) If the change is a pack fact (comp range, a
requirement, a target), update the pack first, with provenance, stamping
`freshness`; then for each affected artifact (per the CONTEXT_PACK.md §5 table),
spawn its agent in update mode: pass the cached content JSON plus the changed pack
paths, instruct it to regenerate ONLY the fields the change touches and return the
full updated content. (b) If the change is purely presentational on one artifact (a
retitle, a deleted optional), and the mapping is one content field to one slot with
no dependent prose, patch the content JSON yourself and say so. Then re-render,
re-verify, deliver via update_artifact. Never edit rendered HTML.
