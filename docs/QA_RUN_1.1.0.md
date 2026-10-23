# QA run for 1.1.0 (2026-10-21)

One full kit run against the 1.1.0 working tree, driven by hand the way the orchestrator
skill drives it: relay (plan), scout (pack), all eight artifact agents in parallel, strict
render, machine verify, QA gate. Every agent ran as a sub-agent on the model its agent file
names, reading its own agent file and compiled brief from this tree. What this run does not
exercise: the plugin loader itself (installing the `.plugin` in Claude Code or Cowork), which
is a click the maintainer makes on the release.

Synthetic role, no client data: Senior Embedded Software Engineer at Onepromptman, Los
Angeles hybrid, one work-authorization constraint, recruiter-stated base range. The profile,
intake note, pack and every content file live outside the repo. No candidate or client names
appear in any output.

## Result

| Step | Outcome |
|---|---|
| relay, plan mode (haiku) | Correct plan: no pack, full scout, eight agents parallel, QA gate on; five ask-first items, one blocking (company proof points) |
| scout, full build (sonnet) | pack.json and pack-research.json written; validate-pack PASS; 12 web calls, at budget |
| orchestrator | constraints copied verbatim into the pack; snapshot into the run folder; ask-first answered and recorded in inputs |
| atlas (sonnet) | NEED_INPUT halt, correct: `comp.by_level` absent. Sectional scout run added the one grounded row and refused to invent a ladder; atlas re-ran on it with a stated reason |
| shakespeare (sonnet) | proceeded on the orchestrator's proof-point waiver; `proof_points: []` written as the honest empty state |
| jdbot (haiku) | strict render failed on `jd.eeo` and `jd.benefits` (no brand document); recruiter supplied both lines in inputs; patch filled them verbatim |
| interview-lab (sonnet) | strict render failed on synthetic slot `doc.prose0`; patch filled it |
| five agents | omitted the top-level `artifact` id, which the renderer keys the handoff consumers line on; set mechanically, and the brief builder now states the envelope explicitly |
| strict render, all eight | OK after the patches above |
| machine verify, all eight | one HIGH each, all the same cause (below); no other HIGH |
| QA gate (opus) | see the verdict section |

## The one verifier HIGH, explained

`render.py verify` flags "surviving example text" whenever an element's text matches the
worked example's domain words (`propulsion`, `spacecraft`, `onepromptman`, and a few more).
The test client is Onepromptman, a propulsion company, so the kit's own footer credit, the
role's "propulsion controller firmware", and a pack requirement named "Spacecraft or
satellite experience" all trip it. A real client in the same domain would trip it the same
way. This is a 1.0.3 verifier limitation, unchanged in 1.1.0 (no renderer code changed), and
it is recorded here rather than silenced.

## Findings against the kit (not caused by 1.1.0, found by this run)

Items 1 and 3 below were fixed in 1.1.0 before tagging (scout's spend rule and JD-Bot's
NEED_INPUT halt for the EEO and benefits lines); the rest stand as recorded.

1. `validate-pack` budgets 12 web calls per pack but counts `web_calls_used` cumulatively, so a
   sectional refresh after a full build always fails the budget check. The honest count (16)
   was kept and the finding recorded in `pack.caveats`.
2. The content-JSON envelope (`template`, `artifact`, `generated`, ...) was shown only inside
   the shared core's shape example; five of eight agents omitted `artifact`. The 1.1.0 brief
   builder now prints the envelope in every schema summary, with the artifact's own number.
3. With no brand document connected, jdbot cannot fill `jd.eeo` and `jd.benefits` and deletes
   them, which strict render refuses. The right path is a NEED_INPUT ask for the two lines;
   the agent file says "never author these yourself" but not "halt and ask". Worth a one-line
   fix in a later release.
4. The compiled brief's word bands are exact counts; several agents reported boolean strings
   and graded answer bars cannot meet them and treated the bands as guidance, as the shared
   core allows.

5. The QA gate's harness observations, all pre-existing and left for a follow-up release:
   the shipped example content for TK_01, TK_07 and TK_08 carries hand-styled pill HTML that
   the brief forbids, so producers copy it; TK_08's compensation row has no proper slot;
   the shakespeare agent file and the TK_05 example disagree on SMS consent from a
   referral-supplied number (a legal call for the maintainer); the ledger floor of 3 rows
   pushes a clean intake toward invented changes; the verifier's example-text check misses a
   reworded example claim while firing on client domain words; the recruiter-screen brief
   does not say to author spot-checks when no question bank is connected; handoff shapes
   vary across producers (`assumptions` string versus list, `generated` empty, branding
   prefixes carried by three agents); TK_07 uses a Gate callout for a non-legal SLA warning.

## Measured context load (scripts/context_budget.py, bytes/4)

| Bucket | 1.0.3 | 1.1.0 |
|---|---|---|
| Resident every session (agent + skill descriptions) | 3,013 | 2,267 |
| Orchestrator skill, main window | 3,422 | 3,195 |
| One fan-out, all eleven agents | 88,913 | 82,111 |

Re-measured with the shipped `context_budget.py` on the final 1.1.0 tree (after the connector
work landed) against a clean 1.0.3 checkout, with the resident bucket now counting description text
only (the rest of the frontmatter is loader configuration): resident 2,588 to 1,841;
orchestrator 3,424 to 3,301; one fan-out 87,430 to 82,576. The table above is the figure recorded on the day of the
run; the changelog carries the re-measured pair.

## QA gate verdict

CERTIFIED on the final re-gate (Opus), after two repair laps.

- Lap 1 returned six HIGH findings across four artifacts: title and must-have drift from the
  pack and an invented change-ledger row (02), a relocation rationale contradicted by its own
  table (03), a heat-grid coverage claim with no question behind it (06), a one-check
  spot-check bank and a reworded worked-example line (08). Each went back to its owning agent
  as a content patch; the four artifacts re-rendered under strict mode.
- Lap 2 confirmed five of six fixes and found three consequential HIGHs from the sixth: the
  screen guide's timing no longer summed to 30 minutes and still described one check, its comp
  line was not the pack's range word for word, and the interview plan's grid was out of step
  with the expanded screen. Both owners patched; both artifacts re-rendered under strict mode.
- Final re-gate: no CRITICAL or HIGH. Six MEDIUM and LOW items remain in the review queue
  (a stale handoff flag on 08, a nice-to-haves touch cell on 06 that 08 does not exercise, no
  time for the spot-check follow-up, two scoring rules that can both fire, one unclear
  pronoun, the disclosed web-budget overage), plus the Estimate figures a human confirms before
  use: the recruiter-stated comp range, 76 days to fill, 17.6 interviews per hire, the TIGHT
  classification and funnel stages, and the SLA defaults.

What this proves about 1.1.0: every agent read its compact brief and produced schema-valid
content; the halt contract, strict render, machine verify and the QA gate all fired where they
should; two laps of owner patches converged. What it does not prove: that 1.0.3 would have
scored differently on the same role (no baseline run was made), or the plugin loader.
