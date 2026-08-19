---
name: talent-one-jd
description: >
  Build the Talent One job description with annotation rail as a polished self-contained HTML document,
  grounded in the user's saved company profile and live market data.
  Use when the user wants a job description or job posting: "write a JD", "job description for [role]", "draft the posting", "job ad". Part of the Talent One kit; for the full kit the talent-one
  skill applies instead.
---

# Talent One — job description with annotation rail

Build artifact 02 (job description with annotation rail) via the Talent One agent pipeline. You never write artifact content yourself.

## Procedure

1. **Profile gate.** Look for `talent-one-profile.md` in the working folder. Missing: offer setup (invoke `talent-one-setup`) or the quick path (collect only what this artifact needs, label assumptions). On the quick path, ALWAYS ask which company this search is for via AskUserQuestion; chat history and memory are not valid sources for company identity, though they may seed the options. Present: read it and confirm its company is the right one for this search in one line.
2. **Plan.** Create or reuse the role home `talent-one-roles/<role_slug>/` with `inputs/` and `content/`, and the run folder `runs/<YYYY-MM-DD>/` with its own `content/`. Legacy `talent-one-runs/` folders stay readable. Before spawning relay, invite materials once in one plain message, never a chip question: paste or attach a JD, intake notes, comp data, or a straight brain dump, or say skip; attached files go into `inputs/` unchanged, pasted text becomes `inputs/braindump-<YYYY-MM-DD>.md` verbatim. Mention, once, the fastest option: pasting `../talent-one/references/PACK_RESEARCH_PROMPT.md` into any Claude chat (claude.ai, the app, or a second Cowork tab) and dropping the returned JSON into `inputs/` gives scout a ready pack to import, optional, never required over the role spec. Spawn the `relay` agent with the requested artifact (02), role home, run folder, profile, per-run inputs, and available connectors. Relay returns the pack plan (reuse / sectional refresh / build / import / migrate), the preflight report, one consolidated ask-first list, and seed proposals. Put those to the user in ONE message; blocking items gate every spawn.

2.5. **Format and source, in the same ask.** In the one AskUserQuestion pass that carries relay's ask-first list, add two items: which format they want (branded HTML, HTML plus markdown, HTML plus docx), and whether they already have a JD or intake doc for this role. If they do, copy the file into `inputs/` and tell relay it is there; accept pasted text too, written to `inputs/braindump-<YYYY-MM-DD>.md` verbatim, invited in one plain message rather than expecting a file. A supplied JD seeds pack paths per `../talent-one/references/CONTEXT_PACK.md` §6 and becomes the intake draft the calibration ledger diffs against; it shortens the pack build, it does not skip the market read.

3. **Execute.** Phase 1: per relay's pack plan, spawn `scout` (scoped to the sections artifact 02 needs per `../talent-one/references/CONTEXT_PACK.md` §5) unless a fresh pack, seeds, or an external import covers it; write accepted seeds into the pack first per §6 (provenance floor, `constraints` verbatim from the profile only), validate with `render.py validate-pack`, snapshot the pack into the run folder. Phase 2: spawn the `jdbot` agent with the run folder, profile, per-run inputs, pack path(s) (`pack.json`), and connector list; it writes `content/02.content.json`, never HTML. Pass `plain_doc: markdown|docx|both` into JD-BOT's prompt when the user asked for a plain document, and name the supplied JD's full path if there is one. JD-BOT writes the markdown beside its content JSON; docx conversion is yours (pandoc, else the `docx` skill; if neither is available, deliver the markdown and say so plainly). Never retype the posting. Phase 3: render and verify deterministically (install beautifulsoup4 if missing: `pip install beautifulsoup4 --break-system-packages`):

   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/scripts/render.py render \
     --template ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/TK_02_Job_Description.dc.html \
     --schema ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/content-schemas/TK_02.content-schema.json \
     --content <run folder>/content/02.content.json \
     --ds ${CLAUDE_PLUGIN_ROOT}/skills/talent-one/references/templates/_ds/seoul-4575df7f-c086-4195-b0df-a53fa16e473e \
     --out <run folder>/02_jdbot.html --handoffs <run folder>/handoffs.json --role <role_slug> --strict
   ```

   then `render.py verify` on the output. `--strict` fails the render (exit 1, a `.failed` artifact, nothing written at `--out`) when a required or synthetic slot is missing, rather than shipping a silently blanked region. A render error, a `--strict` failure, or verify HIGH routes back to `jdbot` as a content patch, never to hand-edited HTML. Deliver the artifact with SendUserFile (then create_artifact per the orchestrator's delivery convention), copy the content JSON to the role home's `content/` cache, and handle NEED_INPUT per the orchestrator's §3.5 rules (batch every ask into one pass; `run_scout` means a sectional pack build).
4. **Self-QA travels with the agent** (00_SHARED_CORE.md §7) and the verify report covers the machine layer; the full qa-gate runs only for multi-artifact packages or on request. Updates to an existing artifact for this role follow the orchestrator's update mode: patch pack or content, re-render, never a full rerun.

## Non-negotiables

Constraints render verbatim from the profile; empty constraints means no eligibility gate. Three-pill honesty vocabulary only. No em dashes. Company facts come from the profile or live research, never invention. Authoritative references live in the `talent-one` skill: `../talent-one/references/00_SHARED_CORE.md`, `CONTEXT_PACK.md`, `02_GROUNDING_MATRIX.md`, and `ADAPTATIONS.md` (items 17-31 define the 1.0 pack-and-render pipeline).
