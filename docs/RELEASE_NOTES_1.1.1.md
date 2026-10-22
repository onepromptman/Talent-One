# Talent One 1.1.1 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents (eight document
specialists plus relay, scout, and QA gate) that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

What is new in 1.1.1 (responsive documents):

- Every rendered document now reads properly on a phone or a narrow window.
  A new stylesheet, `responsive.css`, is inlined into each document by the
  renderer, so the file stays fully self-contained with zero network requests.
- Checked at 390 px (phone) and 768 px (tablet) widths: no horizontal page
  overflow in any of the eight documents. Wide tables and grids reflow or
  scroll inside their own box instead of pushing the page sideways.
- Desktop layout is unchanged.
- No change to agents, content schemas, or the content JSON your existing
  runs hold: re-render a cached run with 1.1.1 and it picks up the responsive
  layout.

SHA-256 of `talent-one-1.1.1.plugin`:
4014d3f2a4e4f28232157081559eaef97fa1db1edbdde6f55b7e2530d259a3ce
