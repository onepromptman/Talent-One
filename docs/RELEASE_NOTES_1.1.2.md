# Talent One 1.1.2 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents (eight document
specialists plus relay, scout, and QA gate) that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

1.1.2 is a hotfix release. It comes from a full end-to-end test on a live role
at a client (2026-10-22): a complete kit run with a simulated recruiter
answering every question, two QA laps, and an update-mode round. Setup, the
company gate, seeding, the ask-first plan, JD compliance catches, and update
mode all held up. The defects below are what the test found.

Fixed

- Renders no longer fail on content shape. The briefs now state the content
  envelope with its types (`standalone_bars` is a list, `optionals` is an
  object, `toggles` is an object), and the renderer coerces empty containers
  of the wrong type (for example `{}` given for `standalone_bars`) with a
  warning. Non-empty wrong shapes still fail, with a message that shows the
  correct literal.
- Synthetic prose slots are documented. Template prose that has no named slot
  of its own is now listed in every agent's brief, with where it sits on the
  page and its word range, so agents fill it first time instead of guessing.
- One kit, one look. The kit mark, the artifact id, and the footer credit were
  written by each agent, so a single run produced eight different mastheads.
  The renderer now owns them (see Added).
- Outreach follows the pack. The outreach agent used its own day grid; it now
  takes cadence from the pack's `channels.sequence_frame`, and any divergence
  is shown on the page. SMS goes out only after the candidate replies and
  supplies the number themselves. A referral is not consent.
- The outreach worked example no longer contradicts the SMS rule.
- Job descriptions keep the title. `jd.title` is the pack's role title
  verbatim, the body uses that title's noun consistently, and any claim about
  the company, team, or cadence must trace to the pack or profile or be left
  out. `jd.title` was widened from exactly 3 words to 2 to 8 words, so real
  titles fit.
- Scout checks its own work before it writes the pack: it recounts every list
  against its stated count, recomputes any figure that states a formula,
  quarantines comp rows older than six months, and date-checks every row used
  in a "posted in window" claim.
- Persona counts line up. Scout's persona range now matches what the talent
  map can show, so nothing is silently dropped.
- The educational brief's worked example no longer carries inline-style
  markup that agents copied and the verifier flagged.

Added

- Renderer flags `--prefix` and `--credit`. The profile's `branding.prefix`
  (company initials, default TK) and `branding.credit` (on or off) are passed
  to the renderer, which stamps the kit mark, the artifact id `<prefix>-NN`,
  and the footer credit "Built with Talent One by Onepromptman" on every
  document. Agents no longer write those.
- Pack size and consistency checks in `validate-pack`: the pack against its
  token budget, the research file against its own, and stated counts against
  list lengths.
- Update mode now searches the cached content files for the old value (and the
  key phrases of a changed assumption) and adds every hit to the set of
  documents to refresh, on top of the pack-section table. A changed number
  quoted in prose no longer gets missed.
- `evals/run_gate.sh`: a public-safe acceptance gate that checks the briefs,
  the context budget, the templates, every worked example (render and verify),
  and repo hygiene, and prints one PASS or FAIL line per step.

Changed

- Setup is shorter and kinder. The eligibility step is split in two: first the
  exact candidate-facing sentence for each constraint, then the gate stage and
  whether a No ends the process. The legal caution and the refusal to invent
  an EEO statement or postal address are unchanged.
- Setup checks brand, benefits, and EEO text against the kit's forbidden-phrase
  list when you hand it over, and offers an edit then, instead of failing later
  at job-description verification.
- The deep-research prompt is demoted in setup to one optional sentence for
  technical users, and the orchestrator now offers it only when the user
  mentions deep research or is clearly technical. The Look step explains
  Dancheong in one line.

Deferred to the next release

- Plain-text export of each outreach email, with a legend for the `[[...]]`
  placeholders.
- The compensation one-pager as a default 07 deliverable.
- A hide-internal toggle for handoff and assumptions blocks.

SHA-256 of `talent-one-1.1.2.plugin`: see docs/INSTALL.md and the .sha256 file
beside the build in `dist/`.
