---
name: talent-one-funnel
description: >
  Diagnose a hiring funnel: compute every stage conversion from the counts by script, compare each
  transition with a benchmark range, name the one broken transition (or say there is no single
  bottleneck), recommend an operational fix, and draft the hiring-manager conversation. Use when the
  user pastes or attaches funnel counts or asks "why aren't we closing this req", "diagnose my funnel",
  "where is my pipeline breaking", "funnel analysis for [role]", "which stage is the bottleneck", or
  "pass-through rates vs benchmark". Part of the Talent One kit; numbers are computed and checked by
  script, the Oracle agent writes the narrative.
---

# Talent One: funnel diagnosis

Turn a funnel into a diagnosis a recruiter can act on. The arithmetic is done and checked by
script before any model writes a word; `talent-one:oracle` writes the narrative; the skill
re-checks every number in it and `talent-one:critic` reviews it. You never write the
diagnosis yourself.

Paths below are relative to this skill folder (`${CLAUDE_PLUGIN_ROOT}/skills/talent-one-funnel`).

## Procedure

1. **Get the funnel.** Accept a CSV in the `data/sample-funnel.csv` shape (stage, count,
   pass_pct_of_prior, role, quarter: cumulative counts in stage order for one role and one
   period), pasted counts, or counts from a connected ATS or reporting tool (see the module's
   `CONNECTORS.md`; read-only, counts only). Write what you received, unchanged except for
   the CSV header, to `talent-one-funnel/<role_slug>/<YYYY-MM-DD>/funnel.csv` in the working
   folder. If role or period is missing, ask once in one AskUserQuestion; never invent them.
   With no funnel at all, offer the synthetic sample (`data/sample-funnel.csv`) as a
   practice run and say it is synthetic.
2. **Verify.** Run
   `python scripts/funnel_verifier.py <run>/funnel.csv --output <run>/verified.json`.
   Exit 2 is invalid input (mixed cohort, counts that increase, a duplicate stage): show the
   message and stop. Exit 1 means a reported percentage disagrees with the counts: tell the
   user which one, and carry on with the computed rates.
3. **Diagnose by script.** Run
   `python scripts/funnel_answer_key.py diagnose <run>/funnel.csv --benchmarks data/teaching-benchmarks.csv --json <run>/diagnosis.json`.
   When the user supplies their own benchmark ranges (same columns as
   `data/teaching-benchmarks.csv`), pass that file instead and say so. Stage names must match
   the benchmark file's `from_stage` and `to_stage`; when they do not, map them with the user
   once (write the mapped CSV, keep the original) rather than guessing.
4. **Narrative.** Dispatch `talent-one:oracle` with the run folder, `verified.json`,
   `diagnosis.json`, the benchmark file, and any `context/*.md` the user keeps in the working
   folder (see `context/README.md`). It writes `<run>/oracle.md`.
5. **Check the narrative's numbers.** Run
   `python scripts/funnel_answer_key.py check-narrative <run>/oracle.md --diagnosis <run>/diagnosis.json`.
   Every percentage and every "N of M" must trace to the diagnosis (or carry a cited source),
   and the bottleneck named must be the computed weakest transition (or "no single
   bottleneck"). On findings, send them back with a dispatch to `talent-one:oracle` as a patch
   request; at most two repair laps, then report what is still open.
6. **Review.** Dispatch `talent-one:critic` with `<run>/oracle.md`, the method
   (`references/oracle-project-prompt.md`) as its rubric, and `funnel.csv`, `verified.json` and
   `diagnosis.json` as its inputs. A RETURNED verdict routes back to the Oracle as a patch,
   inside the same two-lap budget.
7. **Deliver.** Show the diagnosis in chat (table, bottleneck, fix, hiring-manager message,
   counter-argument) and point to `<run>/oracle.md`. When the user wants something a human
   reads next (the hiring-manager note, a candidate update), use the CO-STAR frame in
   `references/candidate-comms-co-star.md`.

## Non-negotiables

- Rates come from the script, never from the supplied percentages and never from the model.
- An offer is not an acceptance; a funnel that stops at offers says acceptance is unknown.
- The benchmark ranges in `data/teaching-benchmarks.csv` are synthesized teaching values, not
  sourced figures: label them so, and prefer the user's own trailing numbers.
- "No single bottleneck" is a valid answer; never force one.
- Real funnel data, competitor notes and sourcing posture stay in the user's working folder
  or a private project; this skill ships only synthetic data and `*.example.md` templates.

## Files

| Path | What it is |
|---|---|
| `scripts/funnel_verifier.py` | Validates one cumulative cohort and recomputes every pass rate (stdlib) |
| `scripts/funnel_answer_key.py` | Transition table, gaps, weakest transition; writes and checks the answer key; checks a narrative |
| `data/sample-funnel.csv` | Synthetic practice funnel (Staff Backend Engineer, 220 applications to 7 offers) |
| `data/teaching-benchmarks.csv` | Benchmark ranges per transition, machine-readable |
| `data/verifier-fixture/` | The verifier's planted-error fixture and its expected report |
| `references/oracle-project-prompt.md` | The method and its generated answer key; also the paste-in edition for a Claude Project |
| `references/oracle-compact.md` | Short DIAGNOSE and BRIEF edition for a project loaded with your own reports |
| `references/teaching-benchmarks.md` | The benchmark ranges as a readable reference |
| `references/funnel-diagnosis-rcar.md`, `references/candidate-comms-co-star.md` | The RCAR (thinking) and CO-STAR (reading) prompt frames |
| `context/` | `*.example.md` templates for your competitor watchlist and sourcing posture |
