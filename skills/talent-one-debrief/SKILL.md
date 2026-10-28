---
name: talent-one-debrief
description: >
  Build the Talent One interviewer briefing and debrief kit as a polished self-contained HTML document:
  per-stage prep cards, bias and legal coaching lines, a structured debrief form, and a decision-meeting
  agenda, grounded in the user's saved company profile and the role's Context Pack.
  Use when the user wants to prep interviewers or run a debrief: "interviewer briefing", "coach my interviewers",
  "debrief form", "decision meeting agenda", "prep the panel for [role]". Part of the Talent One kit; for the
  full kit the talent-one skill applies instead.
---

# Talent One: interviewer briefing and debrief

Build artifact 09 (Interviewer Briefing and Debrief) via the Talent One agent pipeline. You never write artifact content yourself.

## Procedure

1. **Profile gate.** Look for `onepromptman-profile.md` in the working folder. Missing: offer setup (invoke `talent-one-setup`) or the quick path (collect only what this artifact needs, label assumptions). On the quick path, ALWAYS ask which company this search is for via AskUserQuestion; chat history and memory are not valid sources for company identity, though they may seed the options. Present: read it and confirm its company is the right one for this search in one line.
2. **Plan.** Create or reuse the role home `talent-one-roles/<role_slug>/` with `inputs/` and `content/`, and the run folder `runs/<YYYY-MM-DD>/` with its own `content/`. Legacy `talent-one-runs/` folders stay readable. Before spawning relay, invite materials once in one plain message, never a chip question: paste or attach a JD, intake notes, an existing interview plan, or a straight brain dump, or say skip; attached files go into `inputs/` unchanged, pasted text becomes `inputs/braindump-<YYYY-MM-DD>.md` verbatim. Spawn `talent-one:relay` with `mode: plan` plus the requested artifact (09), role home, run folder, profile, per-run inputs, and available connectors. Relay plans only; it spawns nothing. It returns the pack plan (reuse / sectional refresh / build / import / migrate), the preflight report, one consolidated ask-first list, and seed proposals. Put those to the user in ONE AskUserQuestion pass; blocking items gate execution.

3. **Execute.** For every seed the user accepted, write it into the pack yourself first (`../talent-one/references/CONTEXT_PACK.md` §6: provenance floor, `constraints` verbatim from the profile only), validate with `render.py validate-pack`. Spawn `talent-one:relay` with `mode: execute` plus the same inputs and the user's answers or waivers; it spawns `talent-one:scout` if the plan calls for it (scoped to the sections artifact 09 needs per CONTEXT_PACK.md §5: role, spec.requirements, spec.must_have_skills, timing.sla, plus constraints and spec.assessment_methods where used), critiques the pack, spawns `talent-one:interview-coach` (writing `content/09.content.json`, never HTML), spawns `talent-one:critic` on the content and routes repair patches, renders and verifies deterministically via Bash exactly as `agents/relay.md`'s Phase 3 documents (`--strict`; a render error, a `--strict` failure, or a verify HIGH routes back to `talent-one:interview-coach` as a content patch, never hand-edited HTML), and returns the completion report. A single-artifact run never triggers qa-gate (relay's Phase 4 needs 2 or more artifacts). If relay instead returns a consolidated ask block (some agent inside it halted on `ask_user`), put it to the user in one pass and re-invoke `mode: execute` with the answers; never leave an ask unanswered and re-spawn. Deliver the rendered file with SendUserFile (then create_artifact per the orchestrator's delivery convention), and copy the content JSON to the role home's `content/` cache.
4. **Self-QA travels with the agent** (00_SHARED_CORE.md §7) and the verify report covers the machine layer; the full qa-gate runs only for multi-artifact packages or on request. When artifact 06 (Interview Plan) is also being built this run, mention once that the two share no runtime dependency (both read the pack in parallel) but qa-gate cross-checks their stage names when both exist. Updates to an existing artifact for this role follow the orchestrator's update mode: patch pack or content, re-render, never a full rerun.

## Non-negotiables

Constraints render verbatim from the profile; empty constraints means no eligibility gate. Three-pill honesty vocabulary only. No em dashes. Company facts come from the profile or live research, never invention. The seven coaching dimensions (legal guardrails, digging for signal, preparation, running the room, selling the role, rubric nuance, bias awareness) are doctrine: never dropped, never invented past seven. "TBD", "N/A", "to be confirmed", and any hedged placeholder row are QA failures, never shipped content. Authoritative references live in the `talent-one` skill: `../talent-one/references/00_SHARED_CORE.md`, `CONTEXT_PACK.md`, `02_GROUNDING_MATRIX.md`, and `ADAPTATIONS.md` (the content/render-split items define the 1.0 pack-and-render pipeline).
