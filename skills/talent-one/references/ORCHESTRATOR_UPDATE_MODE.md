# Orchestrator: update mode (warm role)

Loaded on demand by the `talent-one` skill, section 5, when the user asks to change or refresh an existing artifact for a role with cached `content/`.

When the user asks to change or refresh an existing artifact for a role that has
`content/` cached: no full run. (a) If the change is a pack fact (comp range, a
requirement, a target), update the pack first, with provenance, stamping
`freshness`; then compute the affected set from the CONTEXT_PACK.md §5 table and
widen it by search: grep the role's cached `content/*.content.json` for the OLD value
of every changed path (the number as written, a spelled-out form such as a number
written as a word, the phrase) and for key phrases of any changed assumption or
decision (a title wording, a named method). Add every artifact with a hit, even when
§5 does not list that path for it: the table covers declared reads, the grep covers
prose that quoted the value. For each affected artifact, spawn its agent in update
mode: pass the cached content JSON, the changed pack paths with old and new values,
and the fields the grep hit, and instruct it to regenerate ONLY the fields the change
touches and return the full updated content. Re-run the grep on the regenerated
content: no hit may remain unless it is deliberate history. The update report lists
every grep hit (artifact, field, old text). (b) If the change is purely presentational on one artifact (a
retitle, a deleted optional), and the mapping is one content field to one slot with
no dependent prose, patch the content JSON yourself and say so. Then re-render,
re-verify, deliver via update_artifact. Never edit rendered HTML.
