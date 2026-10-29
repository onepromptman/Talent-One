#!/usr/bin/env python3
"""Talent One headless runner: the 2.x pipeline as independent `claude -p` sessions.

The plugin runs Talent One inside one Claude Code or Cowork session, with `relay` holding
the loop. This runner runs the same fixed phase structure from a shell, each agent in its
own headless `claude -p` session, coordinated through a local SQLite store:

  1. pack     scout builds the Context Pack (pack.json, pack-research.json) in the role
              home; critic reviews the pack; the runner copies `--constraints-file`
              into the pack verbatim and runs `render.py validate-pack`.
  2. content  every requested artifact agent runs IN PARALLEL against the pack and writes
              <run>/content/<NN>.content.json. There is no inter-artifact dependency
              (CONTEXT_PACK.md section 5); the runner preflights each agent's pack paths.
  2.5 critic  critic per artifact (parallel), verdict PASS or RETURNED.
  3. render   deterministic render + verify with skills/talent-one/scripts/render.py,
              sequentially (render writes the shared compat handoffs.json).
  4. qa       qa-gate over the package when 2 or more artifacts were built.

The runner never writes artifact content and never edits a template. maker != checker
holds by construction: critic and qa-gate are separate sessions on their own model tier.

Delivery gate (fail closed): `run` exits 0 only when every requested artifact has content,
a PASS from critic, a clean render and no HIGH verify finding, the pack critic passed
(when it ran), and qa-gate said CERTIFIED (when 2 or more artifacts were built).
Otherwise it exits 3 and lists the reasons. There is no automatic repair loop: a RETURNED
verdict is recorded and reported for a human to act on.

Usage (from anywhere; paths default to the current directory):
    talent_kit.py init
    talent_kit.py run all --profile onepromptman-profile.md --role-title "Controls Engineer"
    talent_kit.py run 02,06,08 --profile ... --role-title ...   # a subset, still parallel
    talent_kit.py run pack --profile ... --role-title ...       # the Context Pack only
    talent_kit.py report <run_id>
    # add --dry-run to any `run` to assemble prompts and print commands, no calls.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import threading
from contextlib import closing
from pathlib import Path

import runlog

log = runlog.get_logger("talent-one.runner")

HERE = Path(__file__).resolve().parent
MODULE = HERE.parent
SKILL = MODULE / "skills" / "talent-one"
REF = SKILL / "references"
TEMPLATES = REF / "templates"
SCHEMAS = REF / "content-schemas"
RENDER = SKILL / "scripts" / "render.py"
AGENTS_DIR = MODULE / "agents"
MANIFEST = HERE / "agents.json"
DEFAULT_DB = Path(".talent-kit/state.db")

# Tools a headless session never gets: there is no subagent spawning from inside a
# runner session (the runner is the orchestrator) and no MCP server to load.
HEADLESS_DROP = {"Agent", "ToolSearch"}
GATE_FAILED = 3


# --------------------------------------------------------------------------- util
def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "role"


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def die(msg: str, code: int = 1):
    print(f"ERROR  {msg}", file=sys.stderr)
    sys.exit(code)


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_kb_root(config_text: str, config_dir: Path) -> Path | None:
    """Resolve `resources: kb_root:` from an optional runner config file via a constrained
    line scan (no YAML library). The value resolves relative to config_dir. Returns None
    if the block, key, or value is absent, `null`, or empty."""
    in_resources = False
    for line in config_text.splitlines():
        if not in_resources:
            if line.rstrip() == "resources:":
                in_resources = True
            continue
        if line.strip() == "":
            continue
        if not line[:1].isspace():
            break  # dedent: the resources block ended without a kb_root
        m = re.match(r"^\s*kb_root:\s*(.*)$", line)
        if m:
            val = m.group(1).split("#", 1)[0].strip().strip("'\"")
            return (
                (config_dir / val).resolve() if val and val.lower() != "null" else None
            )
    return None


# ------------------------------------------------------------------------- store
class Store:
    """The SQLite state store, safe to use from the runner's worker threads.

    A sqlite3 connection may only be used by the thread that created it. The earlier
    runner opened one connection in the main thread and handed it to every worker of its
    ThreadPoolExecutor, so the first parallel stage died with `sqlite3.ProgrammingError:
    SQLite objects created in a thread can only be used in that same thread`. Here every
    operation opens and closes its own connection (cheap at this volume), and every write
    goes through one lock, so no connection ever crosses a thread and concurrent commits
    never interleave.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self._write_lock, closing(self._connect()) as conn:
            conn.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
            conn.commit()

    def write(self, sql: str, params: tuple = ()):
        with self._write_lock, closing(self._connect()) as conn:
            conn.execute(sql, params)
            conn.commit()

    def read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            return conn.execute(sql, params).fetchall()

    def read_one(self, sql: str, params: tuple = ()):
        rows = self.read(sql, params)
        return rows[0] if rows else None

    # -- domain helpers
    def ensure_run(self, ctx: dict):
        self.write(
            "INSERT OR IGNORE INTO runs (run_id, role_title, role_slug, role_home, run_dir,"
            " profile_path, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                ctx["run_id"],
                ctx["role_title"],
                ctx["slug"],
                str(ctx["role_home"]),
                str(ctx["run_dir"]),
                str(ctx["profile"]) if ctx["profile"] else None,
                now(),
            ),
        )

    def save_session(
        self, run_id, agent, phase, nn, model, session_id, cost, status, verdict=None
    ):
        self.write(
            "INSERT OR REPLACE INTO sessions (run_id, agent, phase, artifact_nn, model,"
            " session_id, cost_usd, status, verdict, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                agent,
                phase,
                nn or "",
                model,
                session_id,
                cost,
                status,
                verdict,
                now(),
            ),
        )

    def save_artifact(self, run_id, nn, agent, status, **fields):
        row = self.read_one(
            "SELECT * FROM artifacts WHERE run_id=? AND artifact_nn=?", (run_id, nn)
        )
        data = dict(row) if row else {}
        data.update({k: v for k, v in fields.items()})
        self.write(
            "INSERT OR REPLACE INTO artifacts (run_id, artifact_nn, agent, content_path,"
            " html_path, verify_path, verify_high, critic_verdict, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                nn,
                agent,
                data.get("content_path"),
                data.get("html_path"),
                data.get("verify_path"),
                data.get("verify_high"),
                data.get("critic_verdict"),
                status,
                now(),
            ),
        )

    def session(self, run_id, agent, phase, nn=""):
        return self.read_one(
            "SELECT * FROM sessions WHERE run_id=? AND agent=? AND phase=? AND artifact_nn=?",
            (run_id, agent, phase, nn or ""),
        )


# ----------------------------------------------------------------- module layout
def agent_file(name: str) -> tuple[dict, str]:
    """(frontmatter, body) of agents/<name>.md. Frontmatter is the flat `key: value` block
    between the first two `---` lines; compile.py stamps `model:` there."""
    path = AGENTS_DIR / f"{name}.md"
    if not path.is_file():
        die(f"agent file not found: {path}")
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        die(f"{path} has no frontmatter block")
    front = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            front[k.strip()] = v.strip()
    return front, m.group(2)


def agent_tools(front: dict) -> list[str]:
    tools = [t.strip() for t in front.get("tools", "").split(",") if t.strip()]
    return [t for t in tools if t not in HEADLESS_DROP]


def system_prompt(name: str) -> str:
    """The agent's body with `${CLAUDE_PLUGIN_ROOT}` resolved to this module, since a
    headless session outside the plugin does not expand it."""
    _, body = agent_file(name)
    return body.replace("${CLAUDE_PLUGIN_ROOT}", str(MODULE))


def template_for(nn: str) -> Path:
    found = sorted(TEMPLATES.glob(f"TK_{nn}_*.dc.html"))
    if len(found) != 1:
        die(
            f"expected exactly one template TK_{nn}_*.dc.html under {TEMPLATES}, found "
            f"{len(found)}"
        )
    return found[0]


def schema_for(nn: str) -> Path:
    return SCHEMAS / f"TK_{nn}.content-schema.json"


def ds_dir() -> Path:
    found = [p for p in (TEMPLATES / "_ds").iterdir() if p.is_dir()]
    if len(found) != 1:
        die(
            f"expected one design-system folder under {TEMPLATES / '_ds'}, found {len(found)}"
        )
    return found[0]


def lookup(pack: dict, research: dict, path: str) -> bool:
    """True when a CONTEXT_PACK.md section 5 path resolves to a present, non-empty value.
    `research:<key>` reads pack-research.json; dotted paths walk nested objects."""
    src = pack
    if path.startswith("research:"):
        src, path = research, path.split(":", 1)[1]
    node = src
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return node not in (None, "", [], {})


# ----------------------------------------------------------------------- claude -p
def claude_command(ctx: dict, agent: str, sysfile: Path, model: str, tools: list[str]):
    cmd = [
        ctx["claude_bin"],
        "-p",
        # APPEND, never --system-prompt: replacing Claude Code's own scaffolding makes
        # an agent loop without terminating (measured in the earlier runner).
        "--append-system-prompt-file",
        str(sysfile),
        # Only the tools this agent declares: unused built-in tool schemas are tens of
        # thousands of tokens per call. --allowedTools pre-approves the survivors so a
        # headless run never blocks on a permission prompt.
        "--tools",
        *tools,
        "--allowedTools",
        ",".join(tools),
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "acceptEdits",
        # No MCP servers and no user-level settings: a company-agnostic run must not
        # inherit someone's global CLAUDE.md, agents or memory.
        "--strict-mcp-config",
        "--exclude-dynamic-system-prompt-sections",
        "--setting-sources",
        "project",
        "--add-dir",
        str(MODULE),
        "--add-dir",
        str(ctx["role_home"]),
    ]
    if ctx["kb_root"] and Path(ctx["kb_root"]).exists():
        cmd += ["--add-dir", str(ctx["kb_root"])]
    return cmd


def head(text: str | None, n: int = 160) -> str:
    """The first n characters of a child's output, on one line: enough to name the
    problem in an error message without copying a whole model reply into logs."""
    flat = " ".join((text or "").split())
    return flat if len(flat) <= n else flat[: n - 3] + "..."


def invoke(ctx: dict, agent: str, label: str, user_msg: str) -> dict:
    """Spawn one headless session for `agent`; return the parsed JSON result."""
    front, _ = agent_file(agent)
    model = ctx["model_override"].get(agent) or front.get("model") or "sonnet"
    tools = agent_tools(front)
    prompts = ctx["run_dir"] / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    sysfile = prompts / f"{label}.system.md"
    sysfile.write_text(system_prompt(agent), encoding="utf-8")
    (prompts / f"{label}.user.md").write_text(user_msg, encoding="utf-8")
    cmd = claude_command(ctx, agent, sysfile, model, tools)
    if ctx["dry_run"]:
        print(
            f"    [dry-run] {label}: model={model} tools={','.join(tools)} "
            f"user message {len(user_msg)} chars"
        )
        print(f"    [dry-run] cmd: {shlex.join(cmd)}")
        return {
            "result": "",
            "session_id": None,
            "total_cost_usd": 0.0,
            "is_error": False,
            "_dry": True,
            "_model": model,
        }
    proc = subprocess.run(
        cmd,
        input=user_msg,
        capture_output=True,
        text=True,
        timeout=ctx["timeout"],
        cwd=str(ctx["role_home"]),
        check=False,
    )
    out = proc.stdout.strip()
    if not out:
        raise RuntimeError(
            f"{label}: claude exited {proc.returncode} with no stdout; "
            f"stderr: {head(proc.stderr)}"
        )
    try:
        res = json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label}: unparseable stdout: {head(out)}") from exc
    if res.get("is_error"):
        raise RuntimeError(
            f"{label}: is_error subtype={res.get('subtype')} "
            f"result={head(str(res.get('result')))}"
        )
    res["_model"] = model
    log.info(
        "session %s: model=%s cost=%s session=%s",
        label,
        model,
        res.get("total_cost_usd"),
        res.get("session_id"),
    )
    return res


def last_verdict(text: str, allowed: tuple[str, ...]) -> str:
    """The last `VERDICT: X` line whose X is allowed; UNKNOWN otherwise (fails the gate)."""
    found = re.findall(r"VERDICT\s*:\s*([A-Z]+)", text or "", re.IGNORECASE)
    for v in reversed(found):
        if v.upper() in allowed:
            return v.upper()
    return "UNKNOWN"


# ---------------------------------------------------------------- prompt builders
def context_block(ctx: dict) -> list[str]:
    kb = ctx["kb_root"]
    connectors = (
        f"- a local KB folder at {kb}, readable with Read/Grep (internal/, benchmarks/, "
        "brand/, history/ by category; see runner/README.md)"
        if kb and Path(kb).exists()
        else "- none: take the standalone public-data path in your grounding-matrix block"
    )
    profile_text = (
        Path(ctx["profile"]).read_text(encoding="utf-8")
        if ctx["profile"] and Path(ctx["profile"]).is_file()
        else "(no profile)"
    )
    return [
        "RUN CONTEXT (Talent One headless runner; you are one session of a fixed pipeline)",
        (
            f"CLAUDE_PLUGIN_ROOT = {MODULE}  (wherever a file you read names "
            "`${CLAUDE_PLUGIN_ROOT}`, it means this directory)"
        ),
        f"role_title: {ctx['role_title']}",
        f"role_slug: {ctx['slug']}",
        f"role home: {ctx['role_home']}",
        f"run folder: {ctx['run_dir']}",
        f"per-run inputs: {ctx['role_home'] / 'inputs'}",
        "connected internal sources:",
        connectors,
        (
            "There is no user channel in this run: a missing input is a NEED_INPUT halt "
            "(shared core section 6.5), never something to invent around."
        ),
        "",
        f"--- profile ({ctx['profile']}) ---",
        profile_text.strip(),
        "--- end profile ---",
        "",
    ]


def pack_paths(ctx: dict, nn: str | None = None) -> list[str]:
    paths = [f"pack: {ctx['run_dir'] / 'pack.json'}"]
    if nn is None or any(
        p.startswith("research:")
        for p in ctx["manifest"]["artifacts"][nn]["pack_paths"]
    ):
        paths.append(f"research: {ctx['run_dir'] / 'pack-research.json'}")
    return paths


def scout_message(ctx: dict) -> str:
    return "\n".join(
        context_block(ctx)
        + [
            (
                "TASK: build the Context Pack for this role (full build, every section any artifact "
                "needs). Write pack.json and pack-research.json into the role home:"
            ),
            f"  {ctx['role_home'] / 'pack.json'}",
            f"  {ctx['role_home'] / 'pack-research.json'}",
            "Never write `constraints` (the runner copies them verbatim from the operator).",
            "Finish with your summary as your final message.",
        ]
    )


def content_message(ctx: dict, nn: str) -> str:
    out = ctx["run_dir"] / "content" / f"{nn}.content.json"
    return "\n".join(
        context_block(ctx)
        + [
            f"TASK: produce the content JSON for artifact {nn}.",
            *pack_paths(ctx, nn),
            f"WRITE YOUR CONTENT JSON TO: {out}",
            (
                "Return your shared core section 6 summary (path, handoff keys, Estimate-pilled "
                "figures, Cautions) as your final message."
            ),
        ]
    )


def critic_message(ctx: dict, nn: str | None, summary: str) -> str:
    if nn is None:
        target = [
            (
                f"ARTIFACT UNDER REVIEW: the Context Pack {ctx['run_dir'] / 'pack.json'} "
                f"(and {ctx['run_dir'] / 'pack-research.json'} where present)"
            ),
            f"RUBRIC: {REF / 'CONTEXT_PACK.md'} sections 3 and 3.5",
        ]
    else:
        target = [
            f"ARTIFACT UNDER REVIEW: {ctx['run_dir'] / 'content' / f'{nn}.content.json'}",
            f"BOUND CONTENT SCHEMA: {schema_for(nn)}",
            *pack_paths(ctx, nn),
        ]
    return "\n".join(
        context_block(ctx)
        + target
        + [
            "PRODUCER SUMMARY:",
            summary.strip() or "(none)",
            "",
            (
                "Run one REFUTE pass. End with exactly one line `VERDICT: PASS` or "
                "`VERDICT: RETURNED`."
            ),
        ]
    )


def qa_message(ctx: dict, built: list[str]) -> str:
    reports = [str(ctx["run_dir"] / "verify" / f"{nn}.verify.json") for nn in built]
    return "\n".join(
        context_block(ctx)
        + [
            f"TASK: audit this package (artifacts {', '.join(built)}).",
            *pack_paths(ctx),
            f"content folder: {ctx['run_dir'] / 'content'}",
            "verify reports:",
            *[f"  {r}" for r in reports],
            "End with exactly one line `VERDICT: CERTIFIED` or `VERDICT: RETURNED`.",
        ]
    )


# ------------------------------------------------------------------------ phases
def phase_pack(ctx: dict, store: Store, reasons: list[str]):
    pack = ctx["role_home"] / "pack.json"
    research = ctx["role_home"] / "pack-research.json"
    if pack.is_file() and not ctx["rebuild_pack"]:
        print(f"  pack: reusing {pack}")
    else:
        print("  pack: scout")
        res = invoke(ctx, "scout", "pack-scout", scout_message(ctx))
        status = "dry-run" if res.get("_dry") else "ok"
        store.save_session(
            ctx["run_id"],
            "scout",
            "pack",
            "",
            res["_model"],
            res.get("session_id"),
            res.get("total_cost_usd"),
            status,
        )
        if res.get("_dry"):
            return
        if not pack.is_file():
            reasons.append("scout wrote no pack.json")
            return
        if ctx["constraints"] is not None:
            data = json.loads(pack.read_text(encoding="utf-8"))
            data["constraints"] = ctx["constraints"]
            pack.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        cmd = [sys.executable, str(RENDER), "validate-pack", "--pack", str(pack)]
        if research.is_file():
            cmd += ["--research", str(research)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            try:
                found = json.loads(proc.stdout).get("findings", [])
                checks = sorted(
                    {f.get("check", "?") for f in found if f.get("severity") == "HIGH"}
                )
                reasons.append(f"validate-pack: HIGH finding(s) {checks}")
            except (json.JSONDecodeError, AttributeError):
                reasons.append(
                    "validate-pack failed: " + (proc.stdout + proc.stderr)[-200:]
                )
        res = invoke(ctx, "critic", "pack-critic", critic_message(ctx, None, ""))
        verdict = last_verdict(res.get("result", ""), ("PASS", "RETURNED"))
        store.save_session(
            ctx["run_id"],
            "critic",
            "pack",
            "",
            res["_model"],
            res.get("session_id"),
            res.get("total_cost_usd"),
            "ok",
            verdict,
        )
        if verdict != "PASS":
            reasons.append(f"pack critic verdict {verdict}")
    for src in (pack, research):
        if src.is_file():
            shutil.copy2(src, ctx["run_dir"] / src.name)


def run_content(ctx: dict, store: Store, nn: str) -> str:
    """Phase 2 for one artifact; runs on a worker thread. Returns the agent's summary."""
    meta = ctx["manifest"]["artifacts"][nn]
    agent = meta["agent"]
    out = ctx["run_dir"] / "content" / f"{nn}.content.json"
    prior = store.session(ctx["run_id"], agent, "content", nn)
    if (
        out.is_file()
        and prior is not None
        and prior["status"] == "ok"
        and not ctx["force"]
    ):
        print(f"  {nn} {agent}: content exists, reusing (--force to redo)")
        return ""
    pack_file = ctx["run_dir"] / "pack.json"
    if pack_file.is_file():
        pack = json.loads(pack_file.read_text(encoding="utf-8"))
        research_file = ctx["run_dir"] / "pack-research.json"
        research = (
            json.loads(research_file.read_text(encoding="utf-8"))
            if research_file.is_file()
            else {}
        )
        missing = [p for p in meta["pack_paths"] if not lookup(pack, research, p)]
        if missing:
            store.save_session(
                ctx["run_id"], agent, "content", nn, None, None, 0.0, "need-input"
            )
            store.save_artifact(ctx["run_id"], nn, agent, "need-input")
            raise NeedInput(f"{nn} {agent}: pack is missing {', '.join(missing)}")
    elif not ctx["dry_run"]:
        raise NeedInput(f"{nn} {agent}: no pack at {pack_file}")
    print(f"  {nn} {agent} ...")
    res = invoke(ctx, agent, f"content-{nn}-{agent}", content_message(ctx, nn))
    status = "dry-run" if res.get("_dry") else "ok"
    store.save_session(
        ctx["run_id"],
        agent,
        "content",
        nn,
        res["_model"],
        res.get("session_id"),
        res.get("total_cost_usd"),
        status,
    )
    store.save_artifact(
        ctx["run_id"],
        nn,
        agent,
        "planned" if res.get("_dry") else "content",
        content_path=str(out),
    )
    return res.get("result", "")


def run_critic(ctx: dict, store: Store, nn: str, summary: str) -> str:
    """Phase 2.5 for one artifact; runs on a worker thread. Returns the verdict."""
    agent = ctx["manifest"]["artifacts"][nn]["agent"]
    res = invoke(ctx, "critic", f"critic-{nn}", critic_message(ctx, nn, summary))
    if res.get("_dry"):
        store.save_session(
            ctx["run_id"], "critic", "critic", nn, res["_model"], None, 0.0, "dry-run"
        )
        return "DRY-RUN"
    verdict = last_verdict(res.get("result", ""), ("PASS", "RETURNED"))
    store.save_session(
        ctx["run_id"],
        "critic",
        "critic",
        nn,
        res["_model"],
        res.get("session_id"),
        res.get("total_cost_usd"),
        "ok",
        verdict,
    )
    row = store.read_one(
        "SELECT status FROM artifacts WHERE run_id=? AND artifact_nn=?",
        (ctx["run_id"], nn),
    )
    store.save_artifact(
        ctx["run_id"],
        nn,
        agent,
        row["status"] if row else "content",
        critic_verdict=verdict,
    )
    return verdict


def render_one(ctx: dict, store: Store, nn: str) -> int:
    """Phase 3 for one artifact; returns the number of HIGH verify findings (-1 on a
    render failure)."""
    agent = ctx["manifest"]["artifacts"][nn]["agent"]
    content = ctx["run_dir"] / "content" / f"{nn}.content.json"
    html = ctx["run_dir"] / f"{nn}_{agent}.html"
    verify = ctx["run_dir"] / "verify" / f"{nn}.verify.json"
    tpl, schema = template_for(nn), schema_for(nn)
    render_cmd = [
        sys.executable,
        str(RENDER),
        "render",
        "--template",
        str(tpl),
        "--schema",
        str(schema),
        "--content",
        str(content),
        "--ds",
        str(ds_dir()),
        "--out",
        str(html),
        "--handoffs",
        str(ctx["run_dir"] / "handoffs.json"),
        "--role",
        ctx["slug"],
        "--strict",
        *ctx["render_args"],
    ]
    verify_cmd = [
        sys.executable,
        str(RENDER),
        "verify",
        "--template",
        str(tpl),
        "--schema",
        str(schema),
        "--doc",
        str(html),
        "--out",
        str(verify),
    ]
    if ctx["dry_run"]:
        print(f"    [dry-run] render: {shlex.join(render_cmd)}")
        print(f"    [dry-run] verify: {shlex.join(verify_cmd)}")
        return 0
    if not content.is_file():
        store.save_artifact(ctx["run_id"], nn, agent, "render-failed")
        return -1
    proc = subprocess.run(render_cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not html.is_file():
        print(
            f"     render failed for {nn}: {(proc.stdout + proc.stderr).strip()[-300:]}"
        )
        store.save_artifact(ctx["run_id"], nn, agent, "render-failed")
        return -1
    verify.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(verify_cmd, capture_output=True, text=True, check=False)
    high = -1
    if verify.is_file():
        findings = json.loads(verify.read_text(encoding="utf-8")).get("findings", [])
        high = sum(1 for f in findings if f.get("severity") == "HIGH")
    store.save_artifact(
        ctx["run_id"],
        nn,
        agent,
        "rendered",
        html_path=str(html),
        verify_path=str(verify),
        verify_high=high,
    )
    log.info("render %s: %s, verify HIGH=%d", nn, html.name, high)
    print(f"     {nn}: rendered {html.name}, verify HIGH={high}")
    return high


class NeedInput(Exception):
    """An artifact agent cannot run: a required pack path is missing."""


def parallel(fn, items, workers):
    """Run fn(item) on worker threads; return {item: result or exception}."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(fn, it): it for it in items}
        for fut in concurrent.futures.as_completed(futs):
            it = futs[fut]
            try:
                results[it] = fut.result()
            except Exception as exc:  # noqa: BLE001  recorded, reported, gate fails
                results[it] = exc
    return results


def parse_targets(target: str, manifest: dict) -> list[str] | None:
    if target == "pack":
        return []
    order = list(manifest["artifacts"])
    if target == "all":
        return order
    wanted = [t.strip() for t in target.split(",") if t.strip()]
    unknown = [t for t in wanted if t not in manifest["artifacts"]]
    if unknown:
        die(
            f"unknown artifact(s) {unknown} (valid: {', '.join(sorted(order))}, all, pack)",
            2,
        )
    return [nn for nn in order if nn in wanted]


def build_context(args) -> dict:
    manifest = load_manifest(Path(args.manifest))
    workdir = Path(args.workdir).resolve()
    role_title = args.role_title or "Role"
    slug = slugify(role_title)
    date = args.date or datetime.date.today().isoformat()
    role_home = workdir / "talent-one-roles" / slug
    run_dir = role_home / "runs" / date
    profile = (
        Path(args.profile).resolve()
        if args.profile
        else workdir / "onepromptman-profile.md"
    )
    if not profile.is_file():
        die(
            f"no profile at {profile}: pass --profile (the company identity is a hard gate)"
        )
    config_text = Path(args.config).read_text(encoding="utf-8") if args.config else ""
    kb_root = (
        Path(args.kb_root).resolve()
        if args.kb_root
        else resolve_kb_root(config_text, Path(args.config).resolve().parent)
        if args.config
        else None
    )
    constraints = None
    if args.constraints_file:
        constraints = json.loads(
            Path(args.constraints_file).read_text(encoding="utf-8")
        )
        if not isinstance(constraints, list):
            die(
                "--constraints-file must hold a JSON list (copied into the pack verbatim)"
            )
    model_override = {}
    for item in args.model or []:
        name, _, model = item.partition("=")
        model_override[name] = model
    return {
        "manifest": manifest,
        "workdir": workdir,
        "role_title": role_title,
        "slug": slug,
        "role_home": role_home,
        "run_dir": run_dir,
        "run_id": args.run_id or f"{slug}-{date}",
        "profile": profile,
        "kb_root": kb_root,
        "constraints": constraints,
        "claude_bin": args.claude_bin
        or os.environ.get("TALENT_KIT_CLAUDE")
        or "claude",
        "timeout": args.timeout,
        "dry_run": args.dry_run,
        "force": args.force,
        "rebuild_pack": args.rebuild_pack,
        "workers": args.max_workers,
        "render_args": shlex.split(args.render_args or ""),
        "model_override": model_override,
    }


def run(args) -> int:
    ctx = build_context(args)
    # log lines carry the runner's own run id; render.py and other children inherit it
    # ctx["run_id"] (<slug>-<date>) is the resume key: a second run the same day reuses the
    # finished artifacts. Log lines carry it plus the start time, so two runs the same day
    # still log apart; render.py and other children inherit that id through RUN_ID.
    log_id = f"{ctx['run_id']}-{datetime.datetime.now().strftime('%H%M%S')}"
    runlog.setup(log_id)
    os.environ["RUN_ID"] = log_id
    targets = parse_targets(args.target, ctx["manifest"])
    for sub in ("content", "verify", "prompts"):
        (ctx["run_dir"] / sub).mkdir(parents=True, exist_ok=True)
    (ctx["role_home"] / "inputs").mkdir(parents=True, exist_ok=True)
    store = Store(Path(args.db))
    store.init()
    store.ensure_run(ctx)
    reasons: list[str] = []
    print(
        f"run '{ctx['run_id']}'  role='{ctx['role_title']}'  run folder={ctx['run_dir']}"
    )

    phase_pack(ctx, store, reasons)
    if not targets:
        return finish(ctx, store, reasons)

    print(f"  content (parallel): {', '.join(targets)}")
    summaries = parallel(
        lambda nn: run_content(ctx, store, nn), targets, ctx["workers"]
    )
    built = []
    for nn in targets:
        got = summaries[nn]
        if isinstance(got, Exception):
            reasons.append(f"content {nn}: {got}")
            print(f"     {nn}: {got}")
        else:
            built.append(nn)

    print(f"  critic (parallel): {', '.join(built) or 'nothing to review'}")
    verdicts = parallel(
        lambda nn: run_critic(ctx, store, nn, summaries[nn]), built, ctx["workers"]
    )
    for nn in built:
        v = verdicts[nn]
        if isinstance(v, Exception) or v not in ("PASS", "DRY-RUN"):
            reasons.append(f"critic {nn}: {v}")

    print("  render + verify (sequential)")
    for nn in built:
        high = render_one(ctx, store, nn)
        if high < 0:
            reasons.append(f"render {nn}: failed")
        elif high > 0:
            reasons.append(f"verify {nn}: {high} HIGH finding(s)")

    if len(built) >= ctx["manifest"]["qa_min_artifacts"]:
        print("  qa-gate")
        try:
            res = invoke(ctx, ctx["manifest"]["qa_agent"], "qa", qa_message(ctx, built))
        except RuntimeError as exc:
            reasons.append(f"qa: {exc}")
        else:
            if res.get("_dry"):
                store.save_session(
                    ctx["run_id"],
                    "qa-gate",
                    "qa",
                    "",
                    res["_model"],
                    None,
                    0.0,
                    "dry-run",
                )
            else:
                (ctx["run_dir"] / "QA_REPORT.md").write_text(
                    res.get("result", ""), encoding="utf-8"
                )
                verdict = last_verdict(res.get("result", ""), ("CERTIFIED", "RETURNED"))
                store.save_session(
                    ctx["run_id"],
                    "qa-gate",
                    "qa",
                    "",
                    res["_model"],
                    res.get("session_id"),
                    res.get("total_cost_usd"),
                    "ok",
                    verdict,
                )
                if verdict != "CERTIFIED":
                    reasons.append(f"qa-gate verdict {verdict}")
    return finish(ctx, store, reasons)


def finish(ctx: dict, store: Store, reasons: list[str]) -> int:
    if ctx["dry_run"]:
        store.write(
            "UPDATE runs SET gate=?, gate_reasons=? WHERE run_id=?",
            ("NOT_EVALUATED", json.dumps(reasons), ctx["run_id"]),
        )
        print("\ndry run: nothing was called; the delivery gate was not evaluated.")
        return 0
    gate = "FAILED" if reasons else "PASSED"
    log.info("delivery gate %s, %d reason(s)", gate, len(reasons))
    store.write(
        "UPDATE runs SET gate=?, gate_reasons=? WHERE run_id=?",
        (gate, json.dumps(reasons), ctx["run_id"]),
    )
    print(f"\ndelivery gate: {gate}")
    for r in reasons:
        print(f"  - {r}")
    return GATE_FAILED if reasons else 0


def report(args) -> int:
    store = Store(Path(args.db))
    r = store.read_one("SELECT * FROM runs WHERE run_id=?", (args.run_id,))
    if not r:
        die(f"no run '{args.run_id}' in {args.db}")
    print(
        f"RUN {r['run_id']}  role={r['role_title']}  created={r['created_at']}  "
        f"gate={r['gate']}"
    )
    total = 0.0
    print("\nSESSION                 PHASE    NN  STATUS      VERDICT    COST")
    for s in store.read(
        "SELECT * FROM sessions WHERE run_id=? ORDER BY created_at", (args.run_id,)
    ):
        total += s["cost_usd"] or 0
        print(
            f"  {s['agent']:20} {s['phase']:8} {s['artifact_nn'] or '--':3} "
            f"{s['status']:11} {s['verdict'] or '':10} ${s['cost_usd'] or 0:.4f}"
        )
    print("\nARTIFACTS")
    for a in store.read(
        "SELECT * FROM artifacts WHERE run_id=? ORDER BY artifact_nn", (args.run_id,)
    ):
        print(
            f"  {a['artifact_nn']} {a['agent']:17} {a['status']:13} "
            f"critic={a['critic_verdict'] or '-'} verify_high={a['verify_high']} "
            f"{a['html_path'] or ''}"
        )
    if r["gate_reasons"]:
        for reason in json.loads(r["gate_reasons"]):
            print(f"  gate: {reason}")
    print(f"\ntotal cost: ${total:.4f}")
    return 0


# ------------------------------------------------------------------------ argparse
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Talent One headless runner")
    p.add_argument("--db", default=str(DEFAULT_DB), help="SQLite state DB path")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create the state DB")

    rp = sub.add_parser(
        "run", help="run `all`, `pack`, one artifact (NN) or a list (02,06)"
    )
    rp.add_argument("target")
    rp.add_argument(
        "--profile",
        help="onepromptman-profile.md (default: <workdir>/onepromptman-profile.md)",
    )
    rp.add_argument(
        "--role-title", help="role being hired for (drives the slug and folders)"
    )
    rp.add_argument("--workdir", default=".", help="where talent-one-roles/ lives")
    rp.add_argument("--date", help="run folder date (default: today)")
    rp.add_argument("--run-id", help="run id (default: <slug>-<date>)")
    rp.add_argument(
        "--config", help="optional runner config; only resources.kb_root is read"
    )
    rp.add_argument("--kb-root", help="local KB folder (overrides --config)")
    rp.add_argument(
        "--constraints-file", help="JSON list copied verbatim into pack.json"
    )
    rp.add_argument("--manifest", default=str(MANIFEST))
    rp.add_argument(
        "--claude-bin",
        help="claude executable (default: $TALENT_KIT_CLAUDE or `claude`)",
    )
    rp.add_argument(
        "--model",
        action="append",
        metavar="AGENT=MODEL",
        help="override one agent's model (repeatable)",
    )
    rp.add_argument("--render-args", help='extra render.py flags, e.g. "--mode dark"')
    rp.add_argument("--max-workers", type=int, default=9, help="parallel sessions")
    rp.add_argument("--timeout", type=int, default=900, help="per-session seconds")
    rp.add_argument(
        "--rebuild-pack", action="store_true", help="run scout even if a pack exists"
    )
    rp.add_argument(
        "--force", action="store_true", help="redo artifacts that already ran"
    )
    rp.add_argument(
        "--dry-run",
        action="store_true",
        help="assemble prompts and print commands; call nothing",
    )

    pr = sub.add_parser(
        "report", help="print a run's sessions, artifacts, gate and cost"
    )
    pr.add_argument("run_id")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    runlog.setup()
    log.debug("talent_kit.py %s", args.cmd)
    if args.cmd == "init":
        Store(Path(args.db)).init()
        print(f"initialized {args.db}")
        return 0
    if args.cmd == "run":
        return run(args)
    return report(args)


if __name__ == "__main__":
    runlog.run(main)
