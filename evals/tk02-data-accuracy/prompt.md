---
name: tk02-data-accuracy
tags: [talent-one, data-accuracy, TK_02]
runs: 10
max_turns: 30
timeout_seconds: 1500
model: claude-sonnet-5
allowed_tools: [Write, Edit, Bash]
---
You are the Talent One orchestrating session for one artifact, run as an eval. Inputs are fixed; do not ask the user anything.

1. Create `./work/roles/harborlight-battery-systems-engineer/inputs/`, `./work/roles/harborlight-battery-systems-engineer/content/`, and `./work/runs/eval/content/`. Copy `./fixtures/pack.json` to `./work/roles/harborlight-battery-systems-engineer/pack.json`.

2. Spawn the `jdbot` agent (Agent tool, subagent type `jdbot`) with this prompt, verbatim plus the absolute paths:

   Run folder: <absolute path of ./work/runs/eval>. Role home: <absolute path of ./work/roles/harborlight-battery-systems-engineer>. Pack: <absolute path of the copied pack.json>. Client profile: company Harborlight Energy, a small home-battery hardware employer; role Battery Systems Engineer (Mid); work model hybrid, distributed, test work onsite; eligibility constraint, verbatim: "Must be authorized to work in the United States; this role does not sponsor visas."; EEO statement, verbatim: "Harborlight Energy is an equal opportunity employer. We consider every qualified applicant without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, disability, or veteran status."; brand voice plain and direct. Produce Artifact 02 content JSON at `<run folder>/content/02.content.json`. Every figure you state must come from the pack; quote `comp.canonical_range` verbatim as the posted range. Do not web-search; the pack is complete for this run.

3. When jdbot returns, copy `./work/runs/eval/content/02.content.json` to `./out/TK_02.content.json` (create `./out/`).

4. Reply with exactly two lines: the path `out/TK_02.content.json`, and jdbot's reported handoff keys.
