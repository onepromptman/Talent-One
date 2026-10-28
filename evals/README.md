# Evals

`run_gate.sh` is the acceptance gate for a Talent One build (ported from Talent One 1.1.3, extended to the ninth artifact). It uses only the kit's own worked examples, never real role or client data.
It checks that the briefs are current, the context budget holds, all 9 templates lint clean, each worked example renders (`--strict`) and verifies with no HIGH finding, and the repo has no em dashes or tracked run files.
Run it from the repository root: `bash evals/run_gate.sh`. It prints one PASS or FAIL line per step and exits nonzero on any failure.
Rendered output and verify reports land in `evals/out/` (gitignored). Verifying an example against itself always trips the "surviving example text" and "identical to example" checks, so those two are excluded from the HIGH count.
Needs Python 3 and a shell; nothing is installed or sent anywhere.

## Model-driven cases

`tk02-data-accuracy/` is the model-layer case for the job description (artifact 02), run by function-core's `evaluate.py --model` (see the system README). Its earlier 3/3-clean result was measured on the previous worked example; the example and the fixture pack were rewritten in 2.1.0, so that proof no longer binds until the case is re-run (a paid run, the owner's call). Results land in `evals/results/` (gitignored).
