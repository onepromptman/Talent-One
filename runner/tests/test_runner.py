"""Tests for the headless runner (talent_kit.py): the thread-safe store, the phase
pipeline end to end against a stubbed `claude`, and the fail-closed delivery gate.

Stdlib unittest, collected by pytest when the module's evals run. Nothing here calls a
model: tests/stub_claude.py stands in for `claude -p`. The render phase shells out to
skills/talent-one/scripts/render.py, which needs beautifulsoup4 (the module's one
declared dependency).
"""

from __future__ import annotations

import io
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER_DIR = HERE.parent
STUB = HERE / "stub_claude.py"
sys.path.insert(0, str(RUNNER_DIR))
import talent_kit

PROFILE = """# onepromptman profile (synthetic test fixture)

company: Example Robotics Co
roles: controls, firmware
"""


def _run(tmp: Path, *extra: str, env: dict | None = None) -> tuple[int, str]:
    """Invoke `talent_kit.py run ...` in-process against the stub; return (exit, stdout)."""
    profile = tmp / "onepromptman-profile.md"
    profile.write_text(PROFILE, encoding="utf-8")
    argv = [
        "--db",
        str(tmp / "state.db"),
        "run",
        *extra,
        "--workdir",
        str(tmp),
        "--profile",
        str(profile),
        "--role-title",
        "Controls Engineer",
        "--date",
        "2026-10-28",
        "--claude-bin",
        str(STUB),
    ]
    out, err = io.StringIO(), io.StringIO()
    old = {k: talent_kit.os.environ.get(k) for k in (env or {})}
    talent_kit.os.environ.update(env or {})
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = talent_kit.main(argv)
    finally:
        for k, v in old.items():
            if v is None:
                talent_kit.os.environ.pop(k, None)
            else:
                talent_kit.os.environ[k] = v
    return code, out.getvalue() + err.getvalue()


def _rows(tmp: Path, sql: str):
    with sqlite3.connect(tmp / "state.db") as conn:
        return conn.execute(sql).fetchall()


class StoreAcrossThreads(unittest.TestCase):
    def test_shared_connection_is_the_bug_this_store_avoids(self):
        """The earlier runner handed one connection to its worker threads; sqlite3
        refuses that. Pin the failure mode so the regression test below means something."""
        with tempfile.TemporaryDirectory() as d:
            conn = sqlite3.connect(Path(d) / "x.db")
            errors = []

            def use():
                try:
                    conn.execute("SELECT 1").fetchall()
                except sqlite3.ProgrammingError as exc:
                    errors.append(exc)

            t = threading.Thread(target=use)
            t.start()
            t.join()
            conn.close()
            self.assertEqual(len(errors), 1)
            self.assertIn("same thread", str(errors[0]))

    def test_store_reads_and_writes_from_many_threads(self):
        with tempfile.TemporaryDirectory() as d:
            store = talent_kit.Store(Path(d) / "state.db")
            store.init()
            errors = []

            def work(i):
                try:
                    for j in range(20):
                        store.save_session(
                            "r",
                            f"agent{i}",
                            "content",
                            f"{j:02d}",
                            "m",
                            None,
                            0.0,
                            "ok",
                        )
                        store.read("SELECT COUNT(*) FROM sessions")
                except Exception as exc:  # noqa: BLE001
                    errors.append(exc)

            threads = [threading.Thread(target=work, args=(i,)) for i in range(9)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertEqual(errors, [])
            self.assertEqual(
                store.read_one("SELECT COUNT(*) AS n FROM sessions")["n"], 180
            )


class ParallelStage(unittest.TestCase):
    def test_dry_run_parallel_stage_02_06_08(self):
        """`run 02,06,08 --dry-run` is the stage the earlier runner died on: its workers
        touched the main thread's connection. Every worker now records its session."""
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            code, out = _run(tmp, "02,06,08", "--dry-run")
            self.assertEqual(code, 0, out)
            self.assertNotIn("ProgrammingError", out)
            rows = _rows(
                tmp,
                "SELECT artifact_nn, status FROM sessions WHERE phase='content'"
                " ORDER BY artifact_nn",
            )
            self.assertEqual(
                rows, [("02", "dry-run"), ("06", "dry-run"), ("08", "dry-run")]
            )
            self.assertIn("dry run: nothing was called", out)

    def test_stubbed_run_of_the_parallel_stage(self):
        """A real (stubbed) run of 02/06/08 with overlapping sessions: content, critic,
        render and verify all land, from worker threads, with no ProgrammingError. The
        stub's content is the shipped worked example, which verify flags as surviving
        example text, so the fail-closed gate must say FAILED and exit 3."""
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            code, out = _run(
                tmp, "02,06,08", "--max-workers", "3", env={"STUB_SLEEP": "0.2"}
            )
            self.assertNotIn("ProgrammingError", out)
            self.assertEqual(code, talent_kit.GATE_FAILED, out)
            run_dir = (
                tmp / "talent-one-roles" / "controls-engineer" / "runs" / "2026-10-28"
            )
            for nn, agent in (
                ("02", "jdbot"),
                ("06", "interview-lab"),
                ("08", "recruiter-screen"),
            ):
                self.assertTrue((run_dir / "content" / f"{nn}.content.json").is_file())
                self.assertTrue((run_dir / f"{nn}_{agent}.html").is_file(), out)
                self.assertTrue((run_dir / "verify" / f"{nn}.verify.json").is_file())
            sessions = _rows(
                tmp,
                "SELECT agent, phase, artifact_nn, status, verdict "
                "FROM sessions ORDER BY phase, artifact_nn, agent",
            )
            phases = [(a, p, n) for a, p, n, _, _ in sessions]
            for nn, agent in (
                ("02", "jdbot"),
                ("06", "interview-lab"),
                ("08", "recruiter-screen"),
            ):
                self.assertIn((agent, "content", nn), phases)
                self.assertIn(("critic", "critic", nn), phases)
            self.assertIn(("qa-gate", "qa", ""), phases)
            self.assertIn(("scout", "pack", ""), phases)
            gate = _rows(tmp, "SELECT gate, gate_reasons FROM runs")[0]
            self.assertEqual(gate[0], "FAILED")
            self.assertTrue(any("HIGH" in r for r in json.loads(gate[1])), gate[1])
            self.assertTrue((run_dir / "QA_REPORT.md").is_file())


class DeliveryGate(unittest.TestCase):
    def test_missing_pack_path_is_need_input_and_fails_the_gate(self):
        """With the bare eval fixture pack (no `timing`), interview-lab cannot preflight:
        it is recorded as need-input, never spawned, and the gate fails."""
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            code, out = _run(tmp, "02,06", env={"STUB_PACK_MINIMAL": "1"})
            self.assertEqual(code, talent_kit.GATE_FAILED, out)
            rows = _rows(
                tmp, "SELECT artifact_nn, status FROM artifacts ORDER BY artifact_nn"
            )
            self.assertIn(("06", "need-input"), rows)
            reasons = json.loads(_rows(tmp, "SELECT gate_reasons FROM runs")[0][0])
            self.assertTrue(any("timing.sla" in r for r in reasons), reasons)

    def test_critic_returned_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            code, out = _run(tmp, "02", env={"STUB_CRITIC": "RETURNED"})
            self.assertEqual(code, talent_kit.GATE_FAILED, out)
            reasons = json.loads(_rows(tmp, "SELECT gate_reasons FROM runs")[0][0])
            self.assertIn("critic 02: RETURNED", reasons)
            self.assertIn("pack critic verdict RETURNED", reasons)

    def test_unknown_verdict_fails_closed(self):
        self.assertEqual(
            talent_kit.last_verdict("looks fine to me", ("PASS", "RETURNED")), "UNKNOWN"
        )
        self.assertEqual(
            talent_kit.last_verdict(
                "VERDICT: PASS\n...\nVERDICT: RETURNED", ("PASS", "RETURNED")
            ),
            "RETURNED",
        )


class Layout(unittest.TestCase):
    def test_every_artifact_resolves_template_schema_and_agent(self):
        manifest = talent_kit.load_manifest()
        self.assertEqual(
            sorted(manifest["artifacts"]),
            ["01", "02", "03", "04", "05", "06", "07", "08", "09"],
        )
        for nn, meta in manifest["artifacts"].items():
            self.assertTrue(talent_kit.template_for(nn).is_file())
            self.assertTrue(talent_kit.schema_for(nn).is_file())
            front, _body = talent_kit.agent_file(meta["agent"])
            self.assertIn("model", front)
            self.assertNotIn(
                "${CLAUDE_PLUGIN_ROOT}", talent_kit.system_prompt(meta["agent"])
            )
        for name in (
            manifest["pack_agent"],
            manifest["critic_agent"],
            manifest["qa_agent"],
        ):
            talent_kit.agent_file(name)
        self.assertTrue(talent_kit.ds_dir().is_dir())

    def test_headless_tools_drop_agent_and_toolsearch(self):
        front, _ = talent_kit.agent_file("jdbot")
        tools = talent_kit.agent_tools(front)
        self.assertNotIn("ToolSearch", tools)
        self.assertNotIn("Agent", tools)
        self.assertIn("Write", tools)


if __name__ == "__main__":
    unittest.main()
