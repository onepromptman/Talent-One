# Changelog

All notable changes to Talent One. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions are semantic.

---

## [1.1.2] · 2026-10-22

Hotfix from a full end-to-end test on a live role at a client (a complete kit run, a simulated recruiter, two QA laps, an update round). sha256 in docs/INSTALL.md.

### Fixed

- **Renders no longer fail on content shape.** The briefs state the content envelope with types (`standalone_bars: []`, `optionals: {}`, `toggles: {}`), and the renderer coerces common near-misses with a warning instead of refusing the document.
- **Synthetic prose slots are documented** in every brief with their place on the page and word range, so agents fill them first time.
- **One kit, one look.** Kit mark, artifact id, and footer credit are renderer-owned, so a run no longer produces eight different mastheads or a stray copyright line.
- **Outreach follows the pack.** Cadence comes from the pack's `channels.sequence_frame`, with any divergence shown on the page. SMS only after the candidate replies and supplies the number; a referral is not consent. The worked example no longer contradicts that rule.
- **Job descriptions keep the title.** `jd.title` is the pack's role title verbatim, the body uses its noun consistently, and any claim about the company, team, or cadence must trace to the pack or profile. Title length limits widened.
- **Scout self-check.** Before writing the pack it recounts lists against stated counts, recomputes figures that state a formula, quarantines comp rows older than six months, and date-checks "posted in window" claims.
- Persona counts match what the talent map can show; the educational brief's example no longer carries inline-style markup.

### Added

- Renderer flags `--prefix` and `--credit`: `branding.prefix` (default TK) and `branding.credit` (on or off) from the profile stamp the kit mark, the artifact id `<prefix>-NN`, and the footer credit "Built with Talent One by Onepromptman" on every document.
- `validate-pack` checks pack and research size against their token budgets, and stated counts against list lengths.
- Update mode greps cached content for the old value and the key phrases of a changed assumption, and refreshes every document that quotes it.
- `evals/run_gate.sh`: a public-safe acceptance gate over briefs, context budget, templates, worked examples, and repo hygiene.

### Changed

- **Shorter setup.** The eligibility step is two smaller asks: the candidate-facing sentence first, then gate stage and whether a No ends the process. The legal caution and the no-invented-EEO-or-address rule stay.
- Setup lints brand, benefits, and EEO text against the forbidden-phrase list at capture and offers an edit then.
- The deep-research prompt is one optional line for technical users; the Look step explains Dancheong in a line.

### Deferred

Outreach plain-text export with a placeholder legend, the comp one-pager as a default 07 deliverable, and a hide-internal toggle for handoff and assumptions blocks.

---

## [1.1.1] · 2026-10-22

Responsive documents. SHA-256 of `talent-one-1.1.1.plugin`:
`4014d3f2a4e4f28232157081559eaef97fa1db1edbdde6f55b7e2530d259a3ce`

### Changed

- **`responsive.css` is inlined into every rendered document**, so each artifact reads on a phone or narrow window with no page overflow at 390 and 768 px. Documents stay self-contained with zero network requests. Desktop layout unchanged.

---

## [1.1.0] · 2026-10-21

A leaner harness, four optional bundled connectors, same output contract. SHA-256 of `talent-one-1.1.0.plugin`:
`d8ec24e499a8e4d589c46a04fbd1c050cae22080290cea861272fb3b2e298e93`

### Changed

- **Agents load less before they work.** Measured with the new `scripts/context_budget.py` on the shipped files: one full fan-out of all eleven agents dropped from 88,913 to 82,111 instruction tokens (about 8 percent); the always-resident agent and skill descriptions from 3,013 to 2,267 tokens (about a quarter); the orchestrator skill from 3,422 to 3,195. No content schema, template, or renderer code changed.
- **Compact shared contract for the eight artifact agents.** `build_briefs.py` compiles the shared rules into each brief once: provenance, the content-JSON shape, and the NEED_INPUT halt contract stay verbatim; preflight, grounding order, voice, constraints, handoff and self-QA are condensed to checklists that keep every auto-fail list word for word. scout and qa-gate keep the full text.
- **Agent files point at their brief** in three sentences instead of a three-paragraph preamble. Every agent description is 25 words or fewer.
- **Orchestrator loads seeding and update-mode procedures on demand** (`references/ORCHESTRATOR_SEEDING.md`, `references/ORCHESTRATOR_UPDATE_MODE.md`); the blocking ask-first gate stays resident.

### Added

- **Four optional bundled connectors** in `.mcp.json`: Exa, Bright Data (four tools), and the official Greenhouse and Ashby MCP servers. None is required; none receives anything until you sign in. `references/CONNECTOR_RUNTIME.md` governs how agents use them, and each agent file carries its own allowlist and denylist so it reaches only those servers and only read tools. See `CONNECTORS.md`.
- **Privacy section** in the README.
- `scripts/context_budget.py`: reports the three context buckets and fails with `--check` when a ceiling is crossed.

### Fixed

- The sourcing playbook's pipeline rates are labeled HOUSE or ORACLE everywhere; the hunter method text said BENCHMARK in three places while the grounding matrix and QA gate said ORACLE.

### Process

An independent review refuted the first draft of these cuts against the source files (four proposed cuts withdrawn before any code changed); a second review of the diff found two gaps, both fixed before testing. One full kit run on a synthetic role, strict render, machine verify and QA gate, two repair laps, certified. Record in [docs/QA_RUN_1.1.0.md](docs/QA_RUN_1.1.0.md).

---

## [1.0.3] · 2026-08-10

Field-reported fix, adversarially verified. SHA-256 of `talent-one-1.0.3.plugin`:
`ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b`

### Fixed

- **Comp charts are now honest by construction.** A user running the kit against a live role found the comp bar charts in the JD and the hiring-manager calibration brief printing hardcoded demo dollar figures from the built-in worked example next to real bars: two comp scales on one page, one of them fiction. Every chart label is now a real content slot, and labels are structurally attached to their own bars, so a printed range can never disagree with the bar it describes.
- The same sweep caught and fixed a leaked demo label in the educational brief's collaboration map.
- **Missing content renders blank, never as leftover demo prose.** If an agent omits a chart label, the document shows an empty label and the render report says exactly what is missing.

### Added

- **Template-furniture lint in the renderer.** Scans every surface where template text can reach a finished document verbatim. Runs at schema build time and inside every machine verify, so hardcoded demo figures cannot ship silently again, in this kit or in templates derived from it.
- Explicit "where it runs" callout across the README, quickstart, and one-pager: Claude Code and Cowork only, not the Claude chat window.

### Process

Two full fix rounds, each fix independently red-teamed (the red team rejected round one's chart fix and forced the stronger labels-ride-bars design), plus a final acceptance gate.

---

## [1.0.2] · 2026-08-07

### Fixed

- Eight confirmed defects from an external defect review, repaired with paired fixer + adversarial advisor passes.
- Verify-scan precision fixes; renderer robustness.

### Added

- **Fully self-contained documents**: zero network requests in any generated artifact.
- Web-budget provenance reporting.
- Per-document skills, so any single artifact can be requested on its own.
- Strict rendering in every documented flow.

---

## [1.0.1] · 2026-08-06

### Fixed

- Synthetic-slot leak.
- Spec patches across artifact schemas.

### Added

- Precompiled agent briefs.
- Scout web-call budget with bundled `baselines.json` fallback.
- Deep-research prompt offer, so a pack can be built in any Claude chat and handed in as a file.

### Verified

- End-to-end retest: QA gate certified all eight artifacts SHIP. Full kit ~30 min cold.

---

## [1.0.0] · 2026-08-03

The architecture rewrite.

### Added

- **Content/render split.** Agents emit content JSON; a deterministic renderer fills the templates. No finished document passes through a model.
- **Context Pack.** One research pass per role, built by the Scout agent, shared by every artifact agent.
- **Parallel artifact agents** against the shared pack.
- **Relay**, the planning broker: reuse a fresh pack, refresh stale sections, seed from supplied material, import an external research file, or build cold from public data.
- Update-in-place re-render from cached content.

### Changed

- Full-kit target cut from ~60 minutes (0.9.x) to 15–20 minutes.

---

## [0.9.x] · 2026-08-02

Initial build. Nine agents, eight artifacts, sequential chain. Tested end-to-end on a Staff Data Engineer role. Not publicly released.
