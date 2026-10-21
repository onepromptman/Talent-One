# Changelog

All notable changes to Talent One. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions are semantic.

---

## [1.1.0] — 2026-10-21

A leaner harness, same output contract. SHA-256 of `talent-one-1.1.0.plugin`:
`a58af64bda84576ad705b44ddd8cba0be8ad53d5acd7496a330297e867246f14`

### Changed

- **Agents load less before they work.** Measured with the new `scripts/context_budget.py` on the shipped files: one full fan-out of all eleven agents dropped from 88,913 to 82,111 instruction tokens (about 8 percent); the always-resident agent and skill descriptions from 3,013 to 2,267 tokens (about a quarter); the orchestrator skill from 3,422 to 3,195. No content schema, template, or renderer code changed.
- **Compact shared contract for the eight artifact agents.** `build_briefs.py` compiles the shared rules into each brief once: provenance (section 3), the content-JSON shape (section 5) and the NEED_INPUT halt contract (section 6.5) stay verbatim; preflight, grounding order, voice, constraints, handoff and self-QA are condensed to checklists that keep every auto-fail list word for word. scout and qa-gate keep the full text.
- **Agent files point at their brief** in three sentences instead of a three-paragraph preamble; the rules that preamble carried now live once in the brief as a runtime contract. Every agent description is 25 words or fewer.
- **Orchestrator loads seeding and update-mode procedures on demand** (`references/ORCHESTRATOR_SEEDING.md`, `references/ORCHESTRATOR_UPDATE_MODE.md`); the blocking ask-first gate stays resident.

### Fixed

- The sourcing playbook's pipeline rates are labeled HOUSE or ORACLE everywhere; the hunter method text said BENCHMARK in three places while the grounding matrix and QA gate said ORACLE.

### Added

- `scripts/context_budget.py`: reports the three context buckets and fails with `--check` when a ceiling is crossed.

### Process

An independent Opus review refuted the first draft of these cuts against the source files (four proposed cuts withdrawn before any code changed). A second Opus review of the diff found two gaps (the constraints wording the QA gate checks, and a missing pointer to the seeding rules on the NEED_INPUT path); both fixed before testing. One full kit run on a synthetic role, strict render, machine verify and QA gate; results in the release pull request.

---

## [1.0.3] — 2026-08-10

Field-reported fix, adversarially verified. SHA-256 of `talent-one-1.0.3.plugin`:
`ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b`

### Fixed

- **Comp charts are now honest by construction.** A user running the kit against a live role found the comp bar charts in the JD and the hiring-manager calibration brief printing hardcoded demo dollar figures from the built-in worked example next to real bars — two comp scales on one page, one of them fiction. Every chart label is now a real content slot, and labels are structurally attached to their own bars, so a printed range can never disagree with the bar it describes.
- The same sweep caught and fixed a leaked demo label in the educational brief's collaboration map.
- **Missing content renders blank, never as leftover demo prose.** If an agent omits a chart label, the document shows an empty label and the render report says exactly what is missing.

### Added

- **Template-furniture lint in the renderer.** Scans every surface where template text can reach a finished document verbatim. Runs at schema build time and inside every machine verify, so hardcoded demo figures cannot ship silently again — in this kit or in templates derived from it.
- Explicit "where it runs" callout across the README, quickstart, and one-pager: Claude Code and Cowork only, not the Claude chat window.

### Process

Two full fix rounds, each fix independently red-teamed (the red team rejected round one's chart fix and forced the stronger labels-ride-bars design), plus a final acceptance gate.

---

## [1.0.2] — 2026-08-07

### Fixed

- Eight confirmed defects from an external defect review, repaired with paired fixer + adversarial advisor passes.
- Verify-scan precision fixes; renderer robustness.

### Added

- **Fully self-contained documents** — zero network requests in any generated artifact.
- Web-budget provenance reporting.
- Per-document skills, so any single artifact can be requested on its own.
- Strict rendering in every documented flow.

---

## [1.0.1] — 2026-08-06

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

## [1.0.0] — 2026-08-03

The architecture rewrite.

### Added

- **Content/render split.** Agents emit content JSON; a deterministic renderer fills the templates. No finished document passes through a model.
- **Context Pack.** One research pass per role, built by the Scout agent, shared by every artifact agent.
- **Parallel artifact agents** against the shared pack.
- **Relay**, the planning broker — reuse a fresh pack, refresh stale sections, seed from supplied material, import an external research file, or build cold from public data.
- Update-in-place re-render from cached content.

### Changed

- Full-kit target cut from ~60 minutes (0.9.x) to 15–20 minutes.

---

## [0.9.x] — 2026-08-02

Initial build. Nine agents, eight artifacts, sequential chain. Tested end-to-end on a Staff Data Engineer role. Not publicly released.
