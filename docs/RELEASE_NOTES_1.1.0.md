# Talent One 1.1.0 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents - eight document
specialists plus relay, scout, and QA gate - that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

What is new in 1.1.0 (a leaner harness, same output contract):

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
- Vocabulary fix: the sourcing playbook labels every pipeline rate HOUSE or
  ORACLE everywhere (the hunter method text said BENCHMARK in three places
  while the grounding matrix and the QA gate said ORACLE).

How it was verified: an independent Opus review refuted the first draft of
these cuts against the source files (four proposed cuts were withdrawn before
any code changed); a second Opus review of the diff found two gaps, both fixed
before testing; then one full kit run (relay, scout, all eight artifact agents,
strict render, machine verify, QA gate) on a synthetic role at Onepromptman,
with the results recorded in the pull request.

SHA-256 of `talent-one-1.1.0.plugin`: a58af64bda84576ad705b44ddd8cba0be8ad53d5acd7496a330297e867246f14
