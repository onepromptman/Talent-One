# Talent One 1.1.0 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents - eight document
specialists plus relay, scout, and QA gate - that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

What is new in 1.1.0 (a leaner harness, same output contract):

- Every agent now loads less instruction text before it starts work. Measured
  on the shipped files with the new `scripts/context_budget.py`: one full
  fan-out of all eleven agents dropped from 87,430 to 82,576 instruction
  tokens, about 6 percent, with no change to the content schemas or the
  templates. The eight artifact agents each read about 1,000
  fewer tokens; the per-session footprint of the plugin (agent and skill
  descriptions resident in every session) dropped from 2,588 to 1,841 tokens,
  about 29 percent, and the orchestrator skill from 3,424 to 3,301.
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
- Vocabulary fix: the sourcing playbook labels every pipeline rate HOUSE or
  ORACLE everywhere (the hunter method text said BENCHMARK in three places
  while the grounding matrix and the QA gate said ORACLE).
- Four connectors ship inside the plugin, none required: Exa (web search and
  page reads, keyless by default), Bright Data (four tools: search results and
  page reads behind bot protection), and the official Greenhouse and Ashby MCP
  servers. The last three sign in with OAuth; the plugin stores no API key.
  Each agent sees only the servers it needs; Ashby's write tools and
  candidate-bearing reads are denied in every agent's configuration, and
  Greenhouse writes are kept off by the admin's scopes, which the plugin
  cannot override. One reference file gives every agent the
  same tool map, budget rule and privacy rules: ATS pipelines are read as counts
  only, no person-profile tool is bundled, and no agent ever writes to an ATS.
  Your own document store or ATS connector works the same way. See CONNECTORS.md.
- Fix: the agent files' tool allowlists had excluded every MCP tool, so a
  subagent could never actually query a connected source; agents now list the
  bundled servers explicitly. JD-Bot asks for the EEO and benefits lines instead of
  deleting the slots, scout reports each run's own web calls so a sectional
  refresh no longer trips the budget check, and the renderer fails cleanly with
  a named field, instead of a Python traceback, when an agent emits a
  malformed content file.

How it was verified: an independent Opus review refuted the first draft of
these cuts against the source files (four proposed cuts were withdrawn before
any code changed); a second Opus review of the diff found two gaps, both fixed
before testing; then one full kit run (relay, scout, all eight artifact agents,
strict render, machine verify, QA gate) on a synthetic role at Onepromptman,
with the results recorded in the pull request.

SHA-256 of `talent-one-1.1.0.plugin`: daf69aba64ecdca63e6e7bbd02f835385929c46845cf89017dc2bd36061f8d5a
