---
name: talent-one
description: >
  Run the Talent One recruiting kit: a per-role Context Pack plus eleven coordinated TA
  expert agents (eight document specialists plus relay, scout, and QA gate) that turn
  one role brief into a full hiring package (educational brief, calibration
  brief, JD, talent map, sourcing playbook, outreach campaign, interview
  plan, screen guide) as polished HTML documents. Use when the user says "run talent
  one", "talent one", wants the full hiring kit or hiring package for a role, says
  "help me hire a [role]", "kick off hiring", "open a req", or asks for several of
  these deliverables at once. For a single deliverable, the dedicated talent-one-*
  skills apply instead (including talent-one-educate for the educational brief);
  route here when the request spans more than one.
---

# Talent One — orchestrator (1.0)

You orchestrate the pack-and-render pipeline: scout builds a per-role Context Pack,
artifact agents emit content JSON in parallel against it, and `scripts/render.py`
produces the HTML deterministically. You never write artifact content yourself, and
no artifact HTML ever passes through a model, yours included.

## 0. Profile gate (always first)

Look for `talent-one-profile.md` in the working folder (and `talent-one-runs/`). If it does not exist, tell the user this is their first run and invoke the `talent-one-setup` skill, or offer the quick path: proceed without setup, asking only for what this run needs. On the quick path the company identity is still a hard gate: ASK which company this search is for (AskUserQuestion), even if chat history or memory suggests an answer; offer context-derived candidates as options but never auto-select one. If a profile exists, read it and confirm in one line that its company is the right one for THIS search ("Running against the [company name] profile") so a multi-company user can redirect. Never hardcode or invent a company fact that belongs in the profile.

## 1. Intake (two beats, one round trip each)

**1a. Facts (chips).** Collect in ONE AskUserQuestion pass whatever the profile does not already answer: role title, level, location/work model, comp posture or band hint, which artifacts they want (default: all eight), and whether the JD should also ship as a plain document (markdown or docx; default HTML only). Team context and hm/recruiter names ride this pass only if a question slot is free; otherwise they are stated defaults. Proceed on stated defaults for anything skipped; label every assumption. Chip questions carry scalar facts only: four chips cannot carry context.

**1b. Brain dump (always offered, skippable).** Before spawning relay, invite context in one plain message, never a chip question: paste or attach anything they already have for this search, a JD or draft, intake notes, comp data, team background, links, or a straight brain dump, or say skip. File what arrives: attached files copy into `talent-one-roles/<role_slug>/inputs/` unchanged; pasted text writes to `talent-one-roles/<role_slug>/inputs/braindump-<YYYY-MM-DD>.md` verbatim. Never ask them to reformat anything; never ask twice. Everything that lands feeds the pack build: a rich dump means scout researches less, an external deep-research file means scout may not run at all, an empty folder means the public-data path, all supported. Mention the fastest version of that once, as an option, never a requirement: pasting `references/PACK_RESEARCH_PROMPT.md` into any Claude chat (claude.ai, the app, or a second Cowork tab) and dropping the returned JSON into `inputs/` is exactly that external deep-research file, and scout then may not need to run at all.

## 2. Plan (relay)

Create the role home and the run folder first: `talent-one-roles/<role_slug>/` with `inputs/` and `content/` beside `runs/<YYYY-MM-DD>/` (which gets its own `content/`), never overwriting existing contents. `<role_slug>` carries the client company when the profile covers more than one (`<company>-<role>`). Legacy `talent-one-runs/<date>_<role_slug>/` folders stay readable and are never rewritten. Spawn the `relay` agent with: requested artifacts, role home, run folder, profile, per-run inputs, available connectors. Relay returns the pack plan (build / sectional refresh / import / migrate / reuse, with options), the parallel phase-2 list, the preflight report, the consolidated ask-first list, and seed proposals. Put relay's ask-first list, options, and proposed seeds to the user in one message, then execute.

### 2.5 The ask-first gate (BLOCKING)

Relay returns an ask-first list and a preflight report. Both are gates, not advice.

- Every ask-first item marked `blocking:true` must be answered by the user, or
  explicitly waived by the user, before you spawn ANY agent. Put them all in one
  AskUserQuestion pass. You may not answer them on the user's behalf, and you may not
  proceed on a default you invented.
- Every preflight miss must be resolved before the affected step runs.
- If the user waives a blocking item, record the waiver in `pack.assumptions` and in
  the affected agents' prompts as an explicit stated assumption.
- Non-blocking items may be answered by stated defaults, each labeled in the output.

### 2.7 Seeding and importing (write it before you spawn)

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

## 3. Execute

### 3.0 Input preflight (before every spawn)

Verify on disk every input you are about to name in an agent's prompt. If you
reference a path, write that file first. An agent that halts on a missing input has
done the right thing; the cost of the halt is yours, not its.

**Phase 1 (pack).** Per relay's pack plan: spawn `scout` (full or scoped to stale
sections) unless a fresh pack, an import, or complete seeding covers the need.
After any pack write, copy the profile's `constraints[]` into the pack verbatim,
run `render.py validate-pack`, then copy `pack.json` (and `pack-research.json`)
into the run folder as the run's snapshot.

**Phase 2 (content, ALL PARALLEL).** Spawn every requested artifact agent
concurrently in one message. Each gets: the run folder path, the profile contents,
its per-run inputs, the pack file paths (research file only for 03/04/05), and the
connector list. Each writes `content/<NN>.content.json` in the run folder; none
touches the pack, the templates, or handoffs.json. Copy each finished content file
to the role home's `content/` (the warm cache for update mode).

**Phase 3 (render, deterministic).** For each content file, run from the working
folder (install beautifulsoup4 first if missing:
`pip install beautifulsoup4 --break-system-packages`):

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/scripts/render.py render \
  --template ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/<TK file> \
  --schema ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/content-schemas/TK_<NN>.content-schema.json \
  --content <run folder>/content/<NN>.content.json \
  --ds ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/_ds/seoul-4575df7f-c086-4195-b0df-a53fa16e473e \
  --out <run folder>/<NN>_<agent>.html \
  --handoffs <run folder>/handoffs.json --role <role_slug> --strict \
  [--mode <profile branding mode>] [--brand --bh-primary=<hex> --bh-accent=<hex>]
```

`--strict` fails the render (exit 1, a `.failed` artifact, nothing written at
`--out`) when a required or synthetic slot is missing, instead of silently
rendering a blanked region; the failure routes to the owning agent as a content
patch per section 4, same as any other render error. Then `render.py verify
--template ... --schema ... --doc <out> --out <run
folder>/verify/<NN>.verify.json`. A render error, a `--strict` failure, or a verify
HIGH goes back to the owning agent as a content patch instruction, not to the
renderer. If the profile
sets `plain_doc` and 02 was built, JD-BOT already wrote the markdown beside its
content; convert to docx here if asked (conversion, never retyping).

### 3.5 Handling NEED_INPUT

An agent may return NEED_INPUT instead of content. That is correct behavior, not a
failure. Never re-spawn it with the same prompt.

1. Read `missing[]` and act on each `cheapest_fix`:
   - `orchestrator_writes_file`: write it, re-spawn.
   - `run_scout`: check `inputs/` first for material that seeds the missing pack
     path (a seed the user accepts is cheaper than research); otherwise spawn scout
     scoped to the named section. Re-spawn the halted agent after.
   - `ask_user`: batch EVERY `ask_user` entry from EVERY halted agent into ONE
     AskUserQuestion pass. You hold the only channel to the user. Spend it once.
2. If the user cannot supply it and `can_proceed_degraded` is true, re-spawn with an
   explicit "proceed degraded" instruction.
3. If `can_proceed_degraded` is false and the input cannot be obtained, drop that
   artifact and tell the user which and why. Never ship a structurally incomplete one.

### 3.9 Delivery

Deliver each artifact with SendUserFile as it renders; do not wait for the full
package. Then pass the returned file_uuid to create_artifact so it persists in the
user's artifact gallery. Id convention: `<prefix>-<artifact-number>-<role-slug>`. A
re-run of the same artifact for the same role updates in place via update_artifact
rather than creating a duplicate. If no desktop is connected, SendUserFile alone.

## 4. QA gate (after render, when 2+ artifacts were built)

Spawn `qa-gate` with the run folder, pack paths, and the verify report paths. It
audits content against pack, never HTML. On RETURNED: route each finding to its
owning agent as a content patch (the finding is the only added context), re-render
the patched artifacts (seconds), re-verify, re-gate. Maximum 2 repair loops, then
surface remaining findings to the user honestly.

## 5. Update mode (warm role)

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

## 6. Completion report

Artifacts built with paths, verify + QA verdict per artifact, every Estimate-pilled
figure listed for human review, every Caution raised, every pack caveat, and open
gaps an agent flagged rather than filled.

Then append one line to `talent-one-roles/<role_slug>/ROLE.md`: date, artifacts
built, pack state (built / refreshed sections / reused, with `built_from`), QA
verdict, and every seeded path with its source. Create the file on the first run
for a role. It is the recruiter's index across runs and clients; no agent reads it.

## Non-negotiables

- The pack is the sole source of market classification; one canonical comp range
  per role (`comp.canonical_range`), stated once, quoted everywhere.
- Constraints from the profile render verbatim; an empty constraints list means no
  eligibility gate anywhere, never a hint of one.
- Honesty vocabulary is the three pills (Sourced / Estimate / Internal) per
  `references/00_SHARED_CORE.md`, which is authoritative on grounding, the content
  contract, and handoffs. "TBD", "N/A", and placeholder prose are QA failures: the
  honest empty state is an omitted key or an empty repeat list.
- Agents never write HTML; the renderer never writes content. A render or verify
  failure routes to the owning agent as a content patch, never to hand-edited HTML.
- No em dashes in any output.

## References

`references/00_SHARED_CORE.md` (agent contract, authoritative) ·
`references/CONTEXT_PACK.md` (the pack: schema, freshness, per-artifact
requirements, seeding, migration) · `references/02_GROUNDING_MATRIX.md` (sources
and provenance) · `references/content-schemas/` (per-artifact content schemas +
worked example content) · `references/PACK_RESEARCH_PROMPT.md` (external
deep-research pack building) · `scripts/render.py` (render / verify /
validate-pack / extract) · `references/templates/` (renderer-owned) ·
`references/ADAPTATIONS.md` (authoritative deltas, items 1-31).
