# Check Talent One with a fictional role

Use an empty working folder. Keep the optional connectors signed out. Record the
revision, date, OS, client version, selected session model, subagent model IDs,
run folder and result. Keep the content, verification JSON and any QA report as
evidence. Run each Claude case in both Claude Code and Cowork before claiming
coverage in both.

## Start with the local check

From the kit folder, using Python 3.10 or later and Bash (Git Bash on Windows):

```bash
python -m pip install pytest
python -m pytest -q
bash evals/run_gate.sh
```

On Windows use Git Bash for the last command. Set `PYTHON` to the test
environment's Python executable if it is not named `python3` on PATH.
The gate renders and verifies all nine bundled examples.
The runner tests exercise a stubbed Claude CLI, including child-process errors
and stale verification reports. These local checks passed on Windows with
synthetic inputs. The chat and live runner cases below are BLOCKED until run
with a signed-in account and approved model usage.

## Claude Code and Cowork

Follow the [install steps](INSTALL.md). Use the client and model access required
by the installed plugin's agent manifests. The maker and checker must resolve to
different models. Record any model override as a separate run.
Production executor and verifier roles use the client's `sonnet` and `opus`
aliases through system-level overrides; the orchestrator retains its explicit
Fable model. Record the exact resolved IDs for all three roles. An unavailable
model or aliases resolving to the same model blocks the run. The pinned kernel
and model-specific eval fixtures remain unchanged.

1. In the empty folder, say `Set up Talent One. Use the fictional company Alder Pattern Labs (alder-pattern.example), a small US packaging-automation employer. Use only these supplied company facts.`
   Answer with fictional values or skip optional fields. Confirm the profile
   exists locally. Repeat setup and confirm the company is reused.
2. Say `Write only a mid-level Industrial Controls Engineer JD for Alder Pattern Labs. Use the supplied facts below, do not browse or use connectors, and ask me for any missing blocking inputs.`
   Supply the same facts on each client:

   > Denver, hybrid with two lab days. Required work: program PLCs, develop
   > safety interlocks and troubleshoot packaging equipment. Helpful: Python
   > for test automation. Annual US base salary range: $105,000 to $125,000.
   > Use a plain voice. Leave unprovided eligibility out. Benefits summary:
   > "Our fictional benefits package includes paid time off and health coverage."
   > Equal-opportunity statement: "Alder Pattern Labs provides equal employment
   > opportunity to all applicants."

   Review the generated content and HTML. Require the supplied band,
   source labels, posting metadata and a traceable decision ledger. Require an
   artifact critique and a fresh verification result with no HIGH findings.
3. In a fresh folder with a copy of the profile, say `Run the full Talent One package for that same fictional role. Use only the supplied facts, ask before assuming a company fact, and do not post a job or contact anyone.`
   Repeat the facts above and supply fictional timing or staffing facts if
   prompted. Supply named, dated fictional research for any requested market,
   persona or benchmark input; label it synthetic and never sourced from the
   live market. An unresolved required pack path must halt with NEED_INPUT;
   that is a passing missing-input case, not a completed package. Once every
   required input is supplied, require nine readable HTML documents, one per artifact, passing
   verification and a final package report. The documents should use consistent role title,
   location, requirements and supplied compensation. Change one role constraint,
   check that the affected drafts update, and compare their claims against the
   new input.
4. In an empty folder, say `Write a JD for a controls engineer. Leave the company unspecified and do not assume it.`
   The session must ask for the company before production. A missing or failing
   renderer must surface as a failure before delivery. The stub suite exercises
   verifier failure with an old passing report already present.
5. Attach [the sample funnel](../skills/talent-one-funnel/data/sample-funnel.csv)
   and say `Diagnose this fictional funnel using the bundled teaching benchmarks.`
   Compare the rates and weakest transition with the diagnosis JSON. Require a
   teaching-data label and no assumption about acceptance when it is absent.

For the separate automated JD model case, use [the eval guide](../evals/README.md)
and [its bundled pack](../evals/fixtures/pack.json). Its older score belongs
to a previous fixture. Use the different role above for normal delivery,
which checks for leaked text from the bundled examples. A pass in the plugin
also requires the client to resolve the installed subagent and tool permissions.

## Claude Code headless runner

Follow the [runner setup](../runner/README.md). Copy the fictional profile from
the setup case into a fresh work folder. Save the role facts above as
`talent-one-roles/industrial-controls-engineer/inputs/brief.md` in that folder.
From the kit folder, with
`WORK` set to the absolute work folder in a Bash shell:

```bash
python runner/talent_kit.py --db "$WORK/state.db" run 02 --workdir "$WORK" \
  --profile "$WORK/onepromptman-profile.md" --role-title "Industrial Controls Engineer" --dry-run
```

Inspect the commands and verify that dry-run launches no model sessions. With
authorized model usage, repeat without `--dry-run`. Require exit 0, the JD HTML,
an artifact critique and a fresh verification result. Repeat with the company
line removed from a copy of the profile. Require nonzero exit and no model
session. Test the legacy Greenhouse fetcher offline with the fixture command
in [the runner guide](../runner/README.md). Compare the counts to the fixture
and verify the export contains no candidate records or identifiers. A live test
requires a sandbox that still has Harvest v1 access. Harvest v3 is UNSUPPORTED
by the fetcher. The plugin's optional MCP connectors are separate. For each
one, sign into a sandbox account, ask for one synthetic source or aggregate
record, confirm its provenance and check that no records were modified. Those
connector runs remain BLOCKED.

The plugin and runner require Claude. A ChatGPT plugin or OpenAI API runner is
UNSUPPORTED.
