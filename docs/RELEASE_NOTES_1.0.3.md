# Talent One 1.0.3 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents - eight document
specialists plus relay, scout, and QA gate - that turn one role brief into a
full 8-document hiring package - calibration brief, JD, talent map, sourcing
playbook, outreach campaign, interview plan, screen guide, and a role
educational brief - as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

What is new in 1.0.3 (field-reported fix, adversarially verified):
- Comp charts are now honest by construction. A user running the kit against
  a live role found that the comp bar charts in the JD and the
  hiring-manager calibration brief printed hardcoded demo dollar figures
  from the kit's built-in worked example next to real bars - two comp scales
  on one page, one of them fiction. Every chart label is now a real content
  slot, and the labels are structurally attached to their own bars, so a
  printed range can never disagree with the bar it describes. The same
  sweep caught and fixed a leaked demo label in the educational brief's
  collaboration map.
- The toolchain now polices this class. The renderer gained a
  template-furniture lint that scans every surface where template text can
  reach a finished document verbatim - it runs at schema build time and
  inside every machine verify, so hardcoded demo figures can never ship
  silently again, in this kit or in templates you derive from it.
- Missing content now renders blank, never as leftover demo prose. If an
  agent omits a chart label, the document shows an empty label and the
  render report says exactly what is missing - it never silently shows the
  worked example's numbers.
- The pattern library, quickstart, one-pager, and this README now teach the
  fixed conventions, including where the kit runs.
- Adversarially reviewed: two full fix rounds, each fix independently
  red-teamed (the red team rejected the first round's chart fix and forced
  the stronger labels-ride-bars design), plus a final acceptance gate.

What was new in 1.0.2: fully self-contained documents (zero network
requests), verify-scan precision fixes, renderer robustness, web-budget
provenance, per-document skills, strict rendering in every documented flow.

SHA-256 of talent-one-1.0.3.plugin:
ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b
