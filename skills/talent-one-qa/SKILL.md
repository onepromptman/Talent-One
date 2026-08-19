---
name: talent-one-qa
description: >
  Build the Talent One QA audit of an existing Talent One package as a polished self-contained HTML document,
  grounded in the user's saved company profile and live market data.
  Use when the user wants the package audited: "QA the kit", "audit these artifacts", "check the package", "talent one QA". Part of the Talent One kit; for the full kit the talent-one
  skill applies instead.
---

# Talent One — QA audit

Audit an existing Talent One run. Find the newest run folder across both layouts, `talent-one-roles/*/runs/*/` and the legacy `talent-one-runs/*/` (or the one the user names; naming a role means the newest run under that role). If none exists, say so and offer to build something instead.

**A 1.0 run** (has `content/*.content.json` and a pack snapshot): if verify reports are missing, generate them first with `render.py verify` per rendered artifact (template + schema from `../talent-one/references/`). Then spawn `qa-gate` with the run folder, the pack paths, the profile, and the verify report paths. It audits content against pack; it never reads HTML.

**A legacy 0.9.x run** (HTML artifacts, no content files): reconstruct the content layer first, one `render.py extract --template <TK file> --schema <TK schema> --doc <artifact>` per artifact into `<run folder>/content/`, and verify each rendered file; there is no pack, so tell qa-gate plainly that pack-fidelity checks are limited to internal consistency plus the run's `handoffs.json`.

Relay qa-gate's verdict, findings with severity and owning agent, and the human-review queue of Estimate-pilled figures. If the user wants fixes applied, route each finding to its owning agent as a content JSON patch (max 2 repair loops), re-render the patched artifacts with `render.py render --strict` (fails the render rather than shipping a silently blanked slot), re-verify, then re-gate once. Never edit rendered HTML by hand.
