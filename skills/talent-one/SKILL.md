---
name: talent-one
description: >
  Run the Talent One recruiting kit: a per-role Context Pack plus thirteen coordinated TA
  expert agents (nine document specialists plus relay, scout, critic, and QA gate) that turn
  one role brief into a full hiring package (educational brief, calibration
  brief, JD, talent map, sourcing playbook, outreach campaign, interview
  plan, screen guide, interviewer briefing and debrief) as polished HTML documents. Use when
  the user says "run talent one", "talent one", wants the full hiring kit or hiring package
  for a role, says "help me hire a [role]", "kick off hiring", "open a req", or asks for
  several of these deliverables at once. For a single deliverable, the dedicated talent-one-*
  skills apply instead (including talent-one-educate for the educational brief);
  route here when the request spans more than one.
---

# Talent One: orchestrator

You run intake and delivery; `relay` runs the pipeline. Spawn `talent-one:relay` with `mode: plan` for the
plan, put its ask-first list to the user, spawn relay `mode: execute` to run it: scout
builds a per-role Context Pack, artifact agents emit content JSON in parallel against it,
critic and qa-gate verify on the opus tier, and `scripts/render.py` produces the HTML
deterministically, all inside relay's own call. You never write artifact content
yourself, and no artifact HTML ever passes through a model, yours or relay's.

## 0. Profile gate (always first)

Look for `onepromptman-profile.md` in the working folder (and `talent-one-runs/`). If it does not exist, tell the user this is their first run and invoke the `talent-one-setup` skill, or offer the quick path: proceed without setup, asking only for what this run needs. On the quick path the company identity is still a hard gate: ASK which company this search is for (AskUserQuestion), even if chat history or memory suggests an answer; offer context-derived candidates as options but never auto-select one. If a profile exists, read it and confirm in one line that its company is the right one for THIS search ("Running against the [company name] profile") so a multi-company user can redirect. Never hardcode or invent a company fact that belongs in the profile.

## 1. Intake (two beats, one round trip each)

**1a. Facts (chips).** Collect in ONE AskUserQuestion pass whatever the profile does not already answer: role title, level, location/work model, comp posture or band hint, which artifacts they want (default: all nine), and whether the JD should also ship as a plain document (markdown or docx; default HTML only). Team context and hm/recruiter names ride this pass only if a question slot is free; otherwise they are stated defaults. Proceed on stated defaults for anything skipped; label every assumption. Chip questions carry scalar facts only: four chips cannot carry context.

**1b. Brain dump (always offered, skippable).** Before spawning relay, invite context in one plain message, never a chip question: paste or attach anything they already have for this search, a JD or draft, intake notes, comp data, team background, links, or a straight brain dump, or say skip. File what arrives: attached files copy into `talent-one-roles/<role_slug>/inputs/` unchanged; pasted text writes to `talent-one-roles/<role_slug>/inputs/braindump-<YYYY-MM-DD>.md` verbatim. Never ask them to reformat anything; never ask twice. Everything that lands feeds the pack build: a rich dump means less research, an empty folder the public-data path, fully supported. Only if they mention deep research or are clearly technical, offer once: pasting `references/PACK_RESEARCH_PROMPT.md` into a Claude chat and dropping the returned JSON into `inputs/` is an external deep-research file, so scout may not need to run.

## 2. Plan (relay, `mode: plan`)

Create the role home and the run folder first: `talent-one-roles/<role_slug>/` with `inputs/` and `content/` beside `runs/<YYYY-MM-DD>/` (which gets its own `content/`), never overwriting existing contents. `<role_slug>` carries the client company when the profile covers more than one (`<company>-<role>`). Legacy `talent-one-runs/<date>_<role_slug>/` folders stay readable and are never rewritten. Spawn the `talent-one:relay` agent with `mode: plan` plus: the working folder as an absolute path, requested artifacts, role home, run folder, profile, per-run inputs, available connectors. The connector list is the profile's `## Connectors` section plus whatever ToolSearch finds live among the bundled servers (`+exa`, `+brightdata`, `+greenhouse`, `+ashby`); a server that is not connected stays off the list, and the agents' rules for using one are in `references/CONNECTOR_RUNTIME.md`. Agents reach only those four servers: anything else the user has connected (a document store, another ATS) you read here, at intake, and file into `inputs/` or the KB. Relay plans only in this mode; it spawns nothing. It returns the pack plan (build / sectional refresh / import / migrate / reuse, with options), the parallel phase-2 list, the preflight report, the consolidated ask-first list, and seed proposals. Put relay's ask-first list, options, and proposed seeds to the user in one AskUserQuestion pass, then move to execution.

### 2.5 The ask-first gate (BLOCKING)

Relay returns an ask-first list and a preflight report. Both are gates, not advice.

- Open with relay's "Already known" list: what the supplied material (brain dump,
  JD, intake notes, profile) answers, each fact with its value. Ask only for what is
  missing; never re-ask a fact the inputs state.
- Every ask-first item marked `blocking:true` must be answered by the user, or
  explicitly waived by the user, before you spawn ANY agent. Put them all in one
  AskUserQuestion pass. You may not answer them on the user's behalf, and you may not
  proceed on a default you invented.
- Every preflight miss must be resolved before the affected step runs.
- If the user waives a blocking item, record the waiver in `pack.assumptions` and in
  the affected agents' prompts as an explicit stated assumption.
- Non-blocking items may be answered by stated defaults, each labeled in the output.

### 2.7 Seeding and importing (write it before you spawn)

When relay proposes seeds, or `inputs/` holds an external deep-research file, read
`references/ORCHESTRATOR_SEEDING.md` and follow it before spawning anything. In short:
seeds write into the pack with provenance at the seed floor, `constraints` copies verbatim
from the profile, and an omitted path stays omitted.

## 3. Execute (relay, `mode: execute`)

Spawn `talent-one:relay` with `mode: execute` plus: the plan relay just returned, the user's
answers to every ask-first item and any explicit waivers, the role home path, the run
folder path, the profile, per-run inputs, and the connector list. Relay now runs the
whole pipeline itself: it spawns `talent-one:scout` when the plan calls for it, spawns every
requested artifact agent in parallel, spawns `talent-one:critic` per artifact and routes repair
patches (at most two laps), renders and verifies each artifact deterministically via
Bash exactly as documented in `agents/relay.md`'s Phase 3, and spawns `talent-one:qa-gate` when 2
or more artifacts were built, writing its report to `<run folder>/QA_REPORT.md` and
routing its findings the same way (at most two laps). You do none of this yourself:
you hold the user channel and the delivery tools, relay holds the loop.

**Handling relay's own NEED_INPUT round-trip.** If relay cannot finish because some
agent inside it halted on `cheapest_fix: ask_user`, it stops and returns ONE
consolidated ask block (every such item, batched, with its partial state: what already
finished, so nothing repeats) instead of a completion report. Put that block to the
user in one AskUserQuestion pass, exactly like the plan's own ask-first gate, then
re-invoke `relay` with `mode: execute` and the same inputs plus the new answers. Never
re-invoke with an unanswered ask still open, and never answer one on the user's behalf.

**Seeding still happens here, before you spawn relay's execute call.** Per §2.7: for
every seed or import the user accepted at the ask-first gate, read the source and
write the accepted pack paths yourself (relay never writes the pack). If the profile
sets `plain_doc` and artifact 02 is in this run, JD-BOT (inside relay's Phase 2) already
writes the posting markdown beside its content; convert to docx here if asked
(conversion, never retyping).

### 3.9 Delivery

Once relay returns the completion report, deliver each artifact from the paths it
names with SendUserFile as you read them; do not wait to re-check anything relay
already verified. Then pass the returned file_uuid to create_artifact so it persists
in the user's artifact gallery. Id convention: `<prefix>-<artifact-number>-<role-slug>`.
A re-run of the same artifact for the same role updates in place via update_artifact
rather than creating a duplicate. If no desktop is connected, SendUserFile alone.

## 5. Update mode (warm role)

When the user asks to change or refresh an existing artifact for a role with cached
`content/`, read `references/ORCHESTRATOR_UPDATE_MODE.md` and follow it: no full run,
pack facts update first with provenance, then widen the section 5 affected set: grep
the role's cached `content/*.content.json` for the OLD value (number, phrase, spelled-out
form) and for key phrases of any changed assumption, add every hit, and list the hits in
the update report. Agents regenerate only the touched fields. Then re-render, re-verify,
deliver via update_artifact. Never edit rendered HTML.

## 6. Completion report

Show the user relay's completion report as-is: artifact paths, critic + verify + QA
verdict per artifact, every Estimate-pilled figure listed for human review, every
Caution raised, every pack caveat, and open gaps an agent flagged rather than filled,
including any finding still open after two repair laps. Then say every document is a
first draft and offer the customization walkthrough (`talent-one-setup` step 8); a
review or customize request goes there, a single value change to §5.

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
and provenance) · `references/content-schemas/` (schemas + worked examples) ·
`references/PACK_RESEARCH_PROMPT.md` · `scripts/render.py` (render / verify /
validate-pack / extract) · `references/templates/` (renderer-owned) ·
`references/ADAPTATIONS.md` (authoritative deltas, the full numbered list) ·
`references/CONNECTOR_RUNTIME.md` (connector tool map, budget, privacy; read only when a
connector is listed).
