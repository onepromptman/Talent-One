# Evals

`run_gate.sh` is the acceptance gate for a Talent One build. It uses only the kit's own worked examples, never real role or client data.
It checks that the briefs are current, the context budget holds, all 8 templates lint clean, each worked example renders (`--strict`) and verifies with no HIGH finding, and the repo has no em dashes or tracked run files.
Run it from the repo root: `bash evals/run_gate.sh`. It prints one PASS or FAIL line per step and exits nonzero on any failure.
Rendered output and verify reports land in `evals/out/` (gitignored). Verifying an example against itself always trips the "surviving example text" and "identical to example" checks, so those two are excluded from the HIGH count.
Needs Python 3 and a shell; nothing is installed or sent anywhere.
