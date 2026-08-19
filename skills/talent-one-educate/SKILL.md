---
name: talent-one-educate
description: >
  Build the Talent One educational brief (role glossary, skills map, career pathways, say-this-not-that cheat sheet)
  as a polished self-contained HTML document, grounded in the user's saved company profile and live market data.
  Use when the user wants to learn a role well enough to speak credibly about it: "educational brief",
  "role primer", "teach me this role", "explain this role to me", "what does a [role] actually do",
  "onboarding brief for the recruiter", "role 101". Part of the Talent One kit; for the full kit the talent-one
  skill applies instead. Not the hiring-manager calibration brief (talent-one-brief).
---

# Talent One — educational brief

Build artifact 01 (educational brief) via the Talent One agent pipeline. You never write artifact content yourself.

## Procedure

1. **Profile gate.** Look for `talent-one-profile.md` in the working folder. Missing: offer setup (invoke `talent-one-setup`) or the quick path (collect only what this artifact needs, label assumptions). On the quick path, ALWAYS ask which company this search is for via AskUserQuestion; chat history and memory are not valid sources for company identity, though they may seed the options. Present: read it and confirm its company is the right one for this search in one line.
2. **Plan.** Create or reuse the role home `talent-one-roles/<role_slug>/` with `inputs/` and `content/`, and the run folder `runs/<YYYY-MM-DD>/` with its own `content/`. Legacy `talent-one-runs/` folders stay readable. Before spawning relay, invite materials once in one plain message, never a chip question: paste or attach a JD, intake notes, comp data, or a straight brain dump, or say skip; attached files go into `inputs/` unchanged, pasted text becomes `inputs/braindump-<YYYY-MM-DD>.md` verbatim. Mention, once, the fastest option: pasting `../talent-one/references/PACK_RESEARCH_PROMPT.md` into any Claude chat (claude.ai, the app, or a second Cowork tab) and dropping the returned JSON into `inputs/` gives scout a ready pack to import, optional, never required over the role spec. Spawn the `relay` agent with the requested artifact (01), role home, run folder, profile, per-run inputs, and available connectors. Relay returns the pack plan (reuse / sectional refresh / build / import / migrate), the preflight report, one consolidated ask-first list, and seed proposals. Put those to the user in ONE message; blocking items gate every spawn.

3. **Execute.** Phase 1: per relay's pack plan, spawn `scout` (scoped to the sections artifact 01 needs per `../talent-one/references/CONTEXT_PACK.md` §5) unless a fresh pack, seeds, or an external import covers it; write accepted seeds into the pack first per §6 (provenance floor, `constraints` verbatim from the profile only), validate with `render.py validate-pack`, snapshot the pack into the run folder. Phase 2: spawn the `sensei` agent with the run folder, profile, per-run inputs, pack path(s) (`pack.json`), and connector list; it writes `content/01.content.json`, never HTML. Phase 3: render and verify deterministically (install beautifulsoup4 if missing: `pip install beautifulsoup4 --break-system-packages`):

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/scripts/render.py render \
     --template ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/TK_01_Educational_Brief.dc.html \
     --schema ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/content-schemas/TK_01.content-schema.json \
     --content <run folder>/content/01.content.json \
     --ds ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/_ds/seoul-4575df7f-c086-4195-b0df-a53fa16e473e \
     --out <run folder>/01_sensei.html --handoffs <run folder>/handoffs.json --role <role_slug> --strict
   ```

   then `render.py verify` on the output. `--strict` fails the render (exit 1, a `.failed` artifact, nothing written at `--out`) when a required or synthetic slot is missing, so a gap is never silently blanked. A render error, a `--strict` failure, or verify HIGH routes back to `sensei` as a content patch, never to hand-edited HTML. Deliver the artifact with SendUserFile (then create_artifact per the orchestrator's delivery convention), copy the content JSON to the role home's `content/` cache, and handle NEED_INPUT per the orchestrator's §3.5 rules (batch every ask into one pass; `run_scout` means a sectional pack build).
4. **Self-QA travels with the agent** (00_SHARED_CORE.md §7) and the verify report covers the machine layer; the full qa-gate runs only for multi-artifact packages or on request. Updates to an existing artifact for this role follow the orchestrator's update mode: patch pack or content, re-render, never a full rerun.

## Non-negotiables

Constraints render verbatim from the profile; empty constraints means no eligibility gate. Three-pill honesty vocabulary only. No em dashes. Company facts come from the profile or live research, never invention. Authoritative references live in the `talent-one` skill: `../talent-one/references/00_SHARED_CORE.md`, `CONTEXT_PACK.md`, `02_GROUNDING_MATRIX.md`, and `ADAPTATIONS.md` (items 17-31 define the 1.0 pack-and-render pipeline).
