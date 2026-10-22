# Talent One 1.1.0 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents (eight document
specialists plus relay, scout, and QA gate) that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

What is new in 1.1.0 (a leaner harness, four optional connectors, same output
contract):

- Every agent now loads less instruction text before it starts work. Measured
  on the shipped files with the new `scripts/context_budget.py`: one full
  fan-out of all eleven agents dropped from 88,913 to 82,111 instruction
  tokens, about 8 percent, with no change to the content schemas, the
  templates, or the renderer. The eight artifact agents each read about 1,000
  fewer tokens; the per-session footprint of the plugin (agent and skill
  descriptions resident in every session) dropped from 3,013 to 2,267 tokens,
  about a quarter, and the orchestrator skill from 3,422 to 3,195.
- The shared rules every artifact agent reads are now a compact contract
  compiled once into its brief (`build_briefs.py`): the provenance rules, the
  content-JSON shape, and the NEED_INPUT halt contract stay verbatim; the
  preflight, grounding order, voice, constraints, handoff, and self-QA
  sections are condensed to checklists that keep every auto-fail list word for
  word. scout and the QA gate keep the full text: scout builds the pack these
  rules protect, and the gate audits against the full rules.
- Agent files carry a three-sentence pointer to their brief instead of a
  three-paragraph preamble; every agent description is 25 words or fewer.
- The orchestrator skill loads its seeding and update-mode procedures only
  when that path runs (`references/ORCHESTRATOR_SEEDING.md`,
  `references/ORCHESTRATOR_UPDATE_MODE.md`).
- `scripts/context_budget.py` reports the three context buckets (resident,
  main window, per-agent bundle) and fails with `--check` when a ceiling is
  crossed, so the numbers cannot drift back.
- Four optional connectors now ship inside the plugin (`.mcp.json`): Exa (web
  research, keyless by default), Bright Data (search results and page reads,
  four tools only), and the official Greenhouse and Ashby MCP servers
  (read-only, pipelines as counts, never candidates). None is required and
  none receives anything until you sign in. `references/CONNECTOR_RUNTIME.md`
  tells the agents how to use whichever are live, and every agent file carries
  its own allowlist and denylist so it reaches only those four servers and
  only the read tools, never your other connectors. See `CONNECTORS.md`.
- The README gained a Privacy section: the plugin sends nothing anywhere, the
  renderer and scripts make no network calls, and what each bundled connector
  may read and never pass on is written down.
- Vocabulary fix: the sourcing playbook labels every pipeline rate HOUSE or
  ORACLE everywhere (the hunter method text said BENCHMARK in three places
  while the grounding matrix and the QA gate said ORACLE).

How it was verified: an independent review refuted the first draft of these
cuts against the source files (four proposed cuts were withdrawn before any
code changed); a second review of the diff found two gaps, both fixed before
testing; then one full kit run (relay, scout, all eight artifact agents,
strict render, machine verify, QA gate) on a synthetic role, two repair laps,
certified by the QA gate. The full record is in [QA_RUN_1.1.0.md](QA_RUN_1.1.0.md).

SHA-256 of `talent-one-1.1.0.plugin`:
d8ec24e499a8e4d589c46a04fbd1c050cae22080290cea861272fb3b2e298e93
