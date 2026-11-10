# Changelog

All notable changes to Talent One. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versions are semantic.

This repository carries the plugin and starts its history at 2.1.0. The paste-in and n8n
swarm editions named below live in the same module of onepromptman/talentai and are
published separately as onepromptman/dag-talent-agents.

---

## [2.1.0] - unreleased

### Release fixes

- **No install at run time.** beautifulsoup4 4.12.3, the renderer's one package, ships
  inside the plugin (`skills/talent-one/scripts/_vendor/`, MIT, licence included), so a
  render never runs pip; relay's install step and the edition's `requirements.txt` are
  gone. A test renders with `python -S` (no site-packages).
- **The runner accepts the profile setup writes.** A profile whose fields sit on bullets
  (`- name: ...`) or in bold was refused with "profile has no company name"; the runner
  now reads all three forms, setup writes the plain `key: value` form, and the plugin
  ships the `PROFILE-SPEC.md` its skills cite.
- **The acceptance gate's hygiene step checks files outside git.** From an unpacked zip
  it used to pass without checking anything; it now checks every file in the folder.
- The `plugin.json` description is 460 characters (the edition's 469), under the
  500-character upload limit; it was 571 and the upload was refused. A test keeps it there.
- Setup walks each connector's OAuth sign-in step by step and runs one read-only check.
- One Python floor everywhere: 3.10 or later.

Carries Talent One 1.1.x (the 1.x line's last release, 1.1.3) forward onto 2.0,
replaces the worked example, and renames the design system for the public
`onepromptman/talentai` home.

### Added

- **Optional connectors.** `.mcp.json` registers four remote MCP servers: Exa and
  Bright Data for the public web layer, Greenhouse and Ashby for the user's ATS.
  `CONNECTORS.md` covers sign-in, scopes, and privacy;
  `skills/talent-one/references/CONNECTOR_RUNTIME.md` tells agents when and how to
  call them. Each agent's tool list names the connector tools it may use; qa-gate
  gets none, and its brief carries no connector line.
- **Renderer-owned chrome.** `render.py render` takes `--prefix` (the artifact code,
  default `TK`) and `--credit on|off` (the footer credit "Built with Talent One by
  OnePromptMan", default on). The renderer fills the kit mark and the left footer
  itself, so `kit.mark` and `footer.left` left the content schemas and
  `SLOT_SCHEMA.json`. Relay passes both flags from the profile's `## Brand` section.
- **Envelope shape checks.** A malformed content envelope (a list where an object
  belongs, an optional given as a bare string) now fails the render with a named
  error instead of rendering blank. `KIT-CORE.md` and the precompiled briefs state the
  envelope rules once.
- **Acceptance gate.** `evals/run_gate.sh` checks the briefs, the context budget,
  template lint, render and verify of all nine worked examples, and repo hygiene,
  then prints GATE PASS or GATE FAIL.
- **Context budget check.** `skills/talent-one/scripts/context_budget.py --check`
  measures the resident skill text and each agent's per-spawn bundle against
  ceilings, re-measured on this tree.
- **Packaging.** `build-plugin.sh` builds `dist/talent-one-<version>.plugin` and its
  SHA-256 from committed files only, and refuses a dirty tree or an existing build.
  No built plugin is committed.
- A responsive stylesheet is inlined into every rendered document, so artifacts read
  on a phone.
- `assets/src/` holds the source of the README hero and a script that rebuilds the
  README images with headless Chrome.
- **Funnel diagnosis.** The `talent-one-funnel` skill and the `oracle` agent: stage
  conversions and the weakest transition come from a script (`funnel_answer_key.py`;
  its `check` command fails when the answer key in the prompt drifts), a
  deterministic funnel verifier checks the narrative's numbers, and the sample funnel
  is corrected (13 of 66 is 19.7%).
- **Prompt Forge.** The `pforge` agent rewrites a recruiter's prompt into a structured,
  testable one.
- **Paste-in and n8n editions of the roster.** `paste-in/` holds the nine agents as
  Claude Project and custom GPT editions with recruiter context guides; `n8n/swarm/`
  holds the agents-as-tools n8n workflow, now behind header authentication on its
  webhook, with output caps raised from 1,024 tokens and the agent loop bounded at 12
  iterations. One source text per agent compiled into all three editions is not built
  yet.
- **Headless runner.** `runner/` runs the kit from the command line with `claude -p`,
  stores sessions in SQLite safely across worker threads, and fetches aggregate ATS
  figures (`ats_fetch.py`). `tools/` holds structural validators for the DAG, the
  templates' fill contract and the slot schema.

### Security

- **Content fragments cannot carry active content.** `render.py` keeps only inline
  formatting from a content `html` fragment: scripts, frames, images, media, SVG, MathML,
  forms and their contents are dropped, other unknown elements are unwrapped,
  event-handler and loader attributes are removed, and links keep only `http(s):`,
  `mailto:` and `#` targets. A `style` survives only when it holds no backslash (CSS
  escapes such as `\75rl(` spell `url(`), comment, at-rule or angle bracket and calls no
  function but `var()`, `rgb()`, `rgba()`, `hsl()`, `hsla()`, `calc()`, `min()`, `max()`
  and `clamp()`; so `url()`, `image-set()`, `-webkit-image-set()`, `cross-fade()` and
  their escaped spellings never reach a document.
- **Brand overrides are design tokens only.** A `brand` override (content `brand` or
  `--brand`) must name an `--op-*` token and hold one plain value under the same style
  rule; any other fails the render, naming each refused override.
- **verify reports what slipped through.** `render.py verify` reports, as a HIGH "active
  content" finding: any script, event handler, loader attribute, SVG, MathML, style
  element, frame, or link other than `http(s):`, `mailto:` and `#` inside a content slot;
  any `javascript:`, `vbscript:` or `data:` link anywhere, however spelled with
  whitespace or case; and any CSS loader (`url()`, `image()`, `image-set()`,
  `cross-fade()`, `element()`, `paint()`, `expression()`, `@import`, a backslash) in any
  `style` attribute, the brand root included. `tests/test_render_safety.py` plants
  hostile fragments, CSS loaders, hostile brand overrides and documents and checks the
  renderer and verify; it also ships in the standalone Talent One repository. The nine
  worked examples render byte-identical to before.
- The missing-dependency message names a flag-free install
  (`python3 -m pip install beautifulsoup4`); the old `--break-system-packages` advice
  fails on the pip that ships with macOS.

### Changed

- The README follows the house shape in about 600 words: who it is for, the tags, where
  it runs and what each path needs, a diagram, a first run, your data, settings, what to
  do when something goes wrong, and a short section for engineers. The detail it carried
  moves to `docs/how-it-works.md`. In the standalone edition the "Built from source"
  note moves to the foot.
- The README says up front what a run needs: Claude Code or Cowork, about 30 minutes in
  a recorded cold run, about 23 model calls before repair laps (the 2 Fable calls are a
  floor), and the four optional services in `.mcp.json`.
- The n8n swarm's emailed deliverable is pinned to plain text with a fixed recipient,
  subject, cc, bcc and reply-to, by a test and the publish gate (which also requires
  exactly one Gmail node), and its README says why the body is not escaped and that a
  repeated webhook request sends another email and spends model calls.
- The headless runner's error messages quote at most a short, one-line head of the
  model's output, and its log lines carry the run id plus the start time, so two runs
  of a role on the same day log apart (the run id that resumes a run is unchanged).
- The engine scripts log through `runlog.py`: a run id on every line, `LOG_LEVEL`,
  `LOG_FORMAT=json` and `LOG_FILE`. What they print for you is unchanged. An error is
  logged with its message and traceback, and `runlog.py` says so.
- ruff lint and format applied, with a `ruff.toml` that keeps the scripts Python
  3.9-compatible; scripts with a shebang are executable.
- The standalone edition ships a CI workflow, `SECURITY.md`, `CONTRIBUTING.md` and a
  `requirements-dev.txt` that adds pytest for its tests.
- **New worked example.** The shipped example is now a fictional Battery Systems
  Engineer search at a fictional home-battery company, Harborlight Energy. All nine
  example contents, the templates' example text, the schemas (regenerated from the
  templates), `SLOT_SCHEMA.json` examples, the contracts, the eval fixture pack, the
  samples, and the README images moved together, with every figure unchanged across
  artifacts. The BLS reference is SOC 17-2199 and the figures are illustrative, not
  current market data. The renderer's surviving-example check (`DOMAIN_MARKERS`)
  tracks the new example's vocabulary.
- **Design system renamed** to the OnePromptMan design system:
  `templates/_ds/onepromptman-ds`, `--op-*` tokens.
- Setup skills are titled "guided setup".
- Licensed MIT, Copyright (c) 2026 OnePromptMan (2.0 was source-available).
- `supersedes:` no longer lists ultimate-rec-assistant (a private repo of the same name): inbound triage, its main
  job, is not covered by this kit.

### Removed

- `docs/TalentOne_Quickstart.pdf` and `docs/TalentOne_OnePager.pdf`. They described
  1.x and had no source to rebuild from; the README and `docs/INSTALL.md` cover the
  same ground.

### Notes

- The tk02 data-accuracy eval's recorded model-run result was produced against the
  old worked example and no longer binds. Re-running it is a paid model run, left for
  the owner to schedule.

## [2.0.0] - 2026-09-06

Rebuilt as a module of the `talentai` system, on the shared function-core (model
tiering, doctrine rules, a machine-checked compliance table). The largest single
change since 1.0's content/render split.

### Added

- **Artifact 09, Interviewer Briefing and Debrief** (Interview Coach, agent code
  A10; A09 is QA Gate). Per-stage interviewer prep cards, the seven bias-and-legal
  coaching dimensions as a fixed doctrine set, a structured four-field debrief form,
  and a decision-meeting agenda. Lineage: folded from the standalone Interview Coach
  expert in dag-talent-agents (published separately as onepromptman/dag-talent-agents); sibling of Interview Lab (which designs
  the loop) rather than a replacement for it. Wired into `CONTEXT_PACK.md` §5,
  `02_GROUNDING_MATRIX.md` Parts 3/3.5/4, `build_briefs.py`'s mapping tables,
  `KIT-CORE.md` §5.1, and a new `talent-one-debrief` single-artifact skill.
- **Relay becomes the orchestrator.** `agents/relay.md` gains `mode: execute`
  alongside its existing `mode: plan`: relay now spawns scout, every requested
  artifact agent (parallel), critic per artifact (REFUTE, at most two repair laps),
  the deterministic renderer and verifier, and qa-gate for multi-artifact packages
  (at most two more laps), then returns the completion report. A `NEED_INPUT`
  halt inside relay's own execute call that only a human can answer stops relay and
  returns one consolidated ask block plus its partial state; the session skill puts
  it to the user once and re-invokes `mode: execute`. `skills/talent-one/SKILL.md`
  and all nine single-artifact skills updated to the two-call shape.
- **Oracle's benchmark-retrieval discipline folded into Scout.** A bounded, named
  sub-step in `agents/scout.md`'s research playbook (Tier-1 user documents, the
  bundled baseline snapshot, then named-publisher web lookups with a HIGH/MEDIUM/LOW
  confidence grade before pilling), feeding the existing `market.macro`,
  `market.funnel`, `comp.canonical_range`, and `comp.by_level` pack paths only.
  Lineage: the standalone Oracle agent in dag-talent-agents (published separately as onepromptman/dag-talent-agents). No new
  top-level pack key.
- **Model tiering, stated and enforced.** Relay orchestrates on `claude-fable-5-1`;
  scout and the nine artifact agents produce on `claude-sonnet-5`; critic and qa-gate
  verify on `claude-opus-5`. function-core's `build/check.py` fails the build if a verifier's
  model matches its producer's, or if `model:` disagrees with an agent's declared
  role.

### Changed

- **Shared profile.** The kit's configuration surface moved from the 1.x per-kit
  profile file to the `talentai` system's shared `onepromptman-profile.md`
  (`PROFILE-SPEC.md`): Organization, Hiring, Constraints, Brand, and Connectors are
  written once by whichever kit's setup runs first; this kit owns only its
  `## Kit: talent-one` block (branding mode, `plain_doc`, `kb_root`, resources).
  `talent-one-setup`'s SKILL.md migrates a legacy per-kit profile into the shared
  file once, on first encounter, and never re-asks a shared field another kit
  already captured.
- **qa-gate's empty-state check hardened.** Check 3b now names "to be confirmed"
  and generic hedge markers explicitly (not just "TBD"/"N/A"/"NOT_FOUND"), and fails
  a one-row repeat that stands in for the missing others, not only a bare
  placeholder string. The nine single-artifact skills' non-negotiables restate the
  same rule.
- Agent, artifact, and document counts updated everywhere they were stated inline
  (module description, `KIT-CORE.md` §1, `SKILL.md` descriptions, README, install
  docs): nine artifacts, thirteen agents.

### Notes

- Talent One 1.x, dag-talent-agents (published separately as onepromptman/dag-talent-agents), ultimate-rec-assistant (a private
  repo of the same name), and an earlier private agent roster are superseded
  (`MODULE.yaml` `supersedes:`).
- Cost consequence of the new verifier tier, stated once: a cold nine-artifact run
  is roughly 10 Sonnet calls (scout plus nine producers) + 11 Opus calls (one pack
  critic pass, nine per-artifact critic passes, plus one qa-gate pass) + 2 Fable
  calls (relay: `mode: plan` then `mode: execute`, plus one more per NEED_INPUT
  round-trip), against 1.x's roughly 11 Sonnet/Haiku calls with no independent
  verification tier at all.

## [1.0.3] - 2026-08-10

Field-reported fix, adversarially verified. SHA-256 of `talent-one-1.0.3.plugin`:
`ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b`

### Fixed

- **Comp charts are now honest by construction.** A user running the kit against a live role found the comp bar charts in the JD and the hiring-manager calibration brief printing hardcoded demo dollar figures from the built-in worked example next to real bars - two comp scales on one page, one of them fiction. Every chart label is now a real content slot, and labels are structurally attached to their own bars, so a printed range can never disagree with the bar it describes.
- The same sweep caught and fixed a leaked demo label in the educational brief's collaboration map.
- **Missing content renders blank, never as leftover demo prose.** If an agent omits a chart label, the document shows an empty label and the render report says exactly what is missing.

### Added

- **Template-furniture lint in the renderer.** Scans every surface where template text can reach a finished document verbatim. Runs at schema build time and inside every machine verify, so hardcoded demo figures cannot ship silently again - in this kit or in templates derived from it.
- Explicit "where it runs" callout across the README, quickstart, and one-pager: Claude Code and Cowork only, not the Claude chat window.

### Process

Two full fix rounds, each fix independently red-teamed (the red team rejected round one's chart fix and forced the stronger labels-ride-bars design), plus a final acceptance gate.

---

## [1.0.2] - 2026-08-07

### Fixed

- Eight confirmed defects from an external defect review, repaired with paired fixer + adversarial advisor passes.
- Verify-scan precision fixes; renderer robustness.

### Added

- **Fully self-contained documents** - zero network requests in any generated artifact.
- Web-budget provenance reporting.
- Per-document skills, so any single artifact can be requested on its own.
- Strict rendering in every documented flow.

---

## [1.0.1] - 2026-08-06

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

## [1.0.0] - 2026-08-03

The architecture rewrite.

### Added

- **Content/render split.** Agents emit content JSON; a deterministic renderer fills the templates. No finished document passes through a model.
- **Context Pack.** One research pass per role, built by the Scout agent, shared by every artifact agent.
- **Parallel artifact agents** against the shared pack.
- **Relay**, the planning broker - reuse a fresh pack, refresh stale sections, seed from supplied material, import an external research file, or build cold from public data.
- Update-in-place re-render from cached content.

### Changed

- Full-kit target cut from ~60 minutes (0.9.x) to 15–20 minutes.

---

## [0.9.x] - 2026-08-02

Initial build. Nine agents, eight artifacts, sequential chain. Tested end-to-end on a Staff Data Engineer role. Not publicly released.
