# Talent One headless runner

Run the Talent One pipeline from a shell, without an interactive session: every agent is
its own headless `claude -p` session, and a local SQLite store records what each one did.
It runs the same fixed phase structure that `agents/relay.md` runs inside the plugin, and
it reads the module's own agents, briefs, schemas, templates and renderer, so there is no
second copy of any prompt to drift.

Use the plugin (`/talent-one`) when a recruiter is in the loop. Use the runner for a
scripted or scheduled run, or to run one artifact cheaply.

## Prerequisites

- The `claude` CLI, installed and signed in.
- Python 3.10+, plus `beautifulsoup4` for the render step (the renderer's one dependency).
- A profile file (`onepromptman-profile.md`, the same one the plugin's setup skill writes).
  The company identity is a hard gate: the runner refuses to start without it.

## Quickstart

```bash
cd runner
python3 talent_kit.py init                                  # creates .talent-kit/state.db

# The full package: pack, nine artifacts in parallel, critic, render, verify, QA.
python3 talent_kit.py run all --profile ../onepromptman-profile.md \
    --role-title "Controls Engineer"

# A subset (still parallel) or one artifact; an existing pack is reused.
python3 talent_kit.py run 02,06,08 --profile ... --role-title "Controls Engineer"

# Only the Context Pack.
python3 talent_kit.py run pack --profile ... --role-title "Controls Engineer"

# See every prompt and command, with no calls and no cost.
python3 talent_kit.py run all --profile ... --role-title "Controls Engineer" --dry-run

python3 talent_kit.py report controls-engineer-2026-10-28   # sessions, verdicts, gate, cost
```

Output follows the plugin's layout, so a runner run and a plugin run of the same role
share one role home: `talent-one-roles/<role_slug>/` holds `pack.json`,
`pack-research.json` and `inputs/`; `runs/<YYYY-MM-DD>/` holds `content/<NN>.content.json`,
the rendered `<NN>_<agent>.html`, `verify/<NN>.verify.json`, `handoffs.json` (the
renderer's compat file), `QA_REPORT.md`, and `prompts/` (every system prompt and user
message the runner sent, for audit).

## Phases

| Phase | What runs | Parallel |
|---|---|---|
| 1. pack | `scout` writes the pack (skipped when one exists, unless `--rebuild-pack`); `--constraints-file` is copied in verbatim; `render.py validate-pack`; `critic` reviews the pack | no |
| 2. content | every requested artifact agent, each writing its content JSON against the pack | yes |
| 2.5 critic | `critic` per artifact, `VERDICT: PASS` or `RETURNED` | yes |
| 3. render | `render.py render --strict`, then `render.py verify` | no (render writes one shared file) |
| 4. qa | `qa-gate` over the package, when 2 or more artifacts were built | no |

There is no inter-artifact dependency (`skills/talent-one/references/CONTEXT_PACK.md`
section 5). Before spawning an artifact agent, the runner checks that every pack path in
that agent's section 5 row is present (`agents.json` mirrors the table, and
`../tools/check_dag.py` keeps the two in step). A missing path is recorded as
`need-input`; that agent is not spawned.

## The delivery gate (fail closed)

`run` exits 0 only when every requested artifact has content, a critic `PASS`, a clean
render and no HIGH verify finding, the pack critic passed (when it ran this time), and
`qa-gate` said `CERTIFIED` (when 2 or more artifacts were built). Otherwise it exits 3 and
prints each reason; `report` shows them again. A verdict line the runner cannot parse
counts as a failure, never a pass.

## How each session is invoked

For every session the runner:

1. builds the **system prompt** from `agents/<name>.md` (the body below the frontmatter),
   with `${CLAUDE_PLUGIN_ROOT}` resolved to this module, and appends it with
   `--append-system-prompt-file`;
2. builds the **user message**: run context (role, role home, run folder, inputs), the
   profile, connected internal sources, the pack paths, and the output path;
3. spawns `claude -p --output-format json --model <model> --tools <tools> --allowedTools
   <tools> --permission-mode acceptEdits --strict-mcp-config
   --exclude-dynamic-system-prompt-sections --setting-sources project --add-dir <module>
   --add-dir <role home> [--add-dir <kb root>]`.

Model and tools come from the agent file's frontmatter, which function-core's
`compile.py` stamps from `MODULE.yaml`, so the runner follows the module's tiers
(`--model AGENT=MODEL` overrides one). `Agent` and `ToolSearch` are dropped: the runner is
the orchestrator, and no MCP server is loaded.

## Cost note

A headless `claude -p` normally inherits a large base context on every call (MCP tool
schemas, the full built-in tool set, dynamic cwd and git sections, user `CLAUDE.md`,
agents and memory). Measured with the earlier version of this runner: about 168K tokens
with MCP servers loaded, trimmed to about 12K by four flags without changing agent
behaviour:

| Flag | Drops |
|---|---|
| `--strict-mcp-config` | every MCP server's tool schemas |
| `--tools <only what the agent declares>` | unused built-in tool schemas |
| `--setting-sources project` | global `CLAUDE.md`, user agents, memory index |
| `--exclude-dynamic-system-prompt-sections` | cwd, git and environment injections |

Do NOT switch to `--system-prompt` (full replace) to go lower: it strips Claude Code's own
agentic scaffolding and an agent can loop without terminating (measured: a calibration run
hung past 9 minutes). Prefer `run <NN>` when you only need one artifact; `report` prints
per-session and total cost.

## Your own data: a local KB folder and the ATS fetch

Pass `--kb-root <dir>` (or `resources.kb_root` in a `--config` file) and the runner adds
that folder to every session and names it as a connected internal source. Lay it out by
category; agents read the folder that fits:

| Folder | Holds |
|---|---|
| `internal/` | calibration notes, hiring guides, past interview plans and talent maps, the approved comp band export (`internal/comp/bands.csv`), and the ATS fetch output below. Cited with the **Internal** provenance pill. |
| `benchmarks/` | benchmark tables you are licensed to use, with source and vintage. Cited with the **Sourced** provenance pill. |
| `brand/` | voice guide, benefits summary and the equal-opportunity statement, verbatim. Read directly, never authored by an agent. |
| `history/` | prior artifacts of the same type, with measured results where known. |

Real KB content is sensitive (bands, candidate data, internal calibration): keep the
folder outside any repository.

`ats_fetch.py` fills `internal/` from Greenhouse Harvest with aggregate, PII-free house
numbers (funnel pass-through with n, accepted-offer comp by level with a 3-offer floor,
time to hire, prior posting language, scorecard structure). The spec is
[`ATS_FETCH_CONTRACT.md`](ATS_FETCH_CONTRACT.md):

```bash
GREENHOUSE_HARVEST_KEY=... python3 ats_fetch.py --provider greenhouse \
    --crosswalk crosswalk.csv --out <kb_root> [--role-family <rf>] [--dry-run]
```

## Not built yet

- **Repair loop.** On `RETURNED` (pack critic, artifact critic, verify HIGH, or QA), the
  plugin's relay re-runs the owning agent with the findings, at most two laps. The runner
  records the verdict, fails the gate and stops there; a human drives the repair (re-run
  the artifact with `--force`).
- **Pack freshness and sectional refresh.** The runner reuses an existing pack as is or
  rebuilds it whole (`--rebuild-pack`); it does not apply the section 4 freshness table.
- **Seeding and import.** Material in `inputs/` is passed to scout as a folder; the
  plugin's seed-and-import step (CONTEXT_PACK.md section 6) does not run here.
- **Constraints from the profile.** The runner copies constraints only from
  `--constraints-file` (a JSON list). Without it the pack carries none, which means no
  eligibility gate anywhere (the honest empty state).
- **A shared store.** State is per-machine SQLite; there is no Postgres adapter.
- **Live runs in CI.** The tests drive the whole pipeline against a stub `claude`
  (`tests/stub_claude.py`); a real run spends model calls and is not part of any gate.

## Files

| File | Role |
|---|---|
| `talent_kit.py` | the runner: phases, headless sessions, SQLite store, delivery gate |
| `agents.json` | the phase manifest: artifact to agent, section 5 pack paths, verifier names |
| `schema.sql` | the state store (runs, sessions, artifacts) |
| `ats_fetch.py`, `ATS_FETCH_CONTRACT.md` | the Greenhouse fetch into a local KB folder |
| `tests/` | unittest suites (collected by pytest in the module's evals) and the `claude` stub |
