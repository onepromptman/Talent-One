"""Tests for the headless runner (talent_kit.py): the thread-safe store, the phase
pipeline end to end against a stubbed `claude`, and the fail-closed delivery gate.

Stdlib unittest, collected by pytest when the module's evals run. Nothing here calls a
model: tests/stub_claude.py stands in for `claude -p`. The render phase shells out to
skills/talent-one/scripts/render.py, which carries its one package (beautifulsoup4)
in its own _vendor/ folder.
"""

from __future__ import annotations

import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
RUNNER_DIR = HERE.parent
STUB = HERE / "stub_claude.py"
sys.path.insert(0, str(RUNNER_DIR))
import talent_kit

PROFILE = """# onepromptman profile (synthetic test fixture)

company: Example Robotics Co
roles: controls, firmware
"""


def _run(
    tmp: Path, *extra: str, env: dict | None = None, profile_text: str = PROFILE
) -> tuple[int, str]:
    """Invoke `talent_kit.py run ...` in-process against the stub; return (exit, stdout)."""
    profile = tmp / "onepromptman-profile.md"
    profile.write_text(profile_text, encoding="utf-8")
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
    original_command = talent_kit.claude_command

    def stub_command(*args, **kwargs):
        cmd = original_command(*args, **kwargs)
        # Windows cannot launch the Python fixture directly.
        if Path(cmd[0]).resolve() == STUB.resolve():
            return [sys.executable, *cmd]
        return cmd

    out, err = io.StringIO(), io.StringIO()
    old = {k: talent_kit.os.environ.get(k) for k in (env or {})}
    talent_kit.os.environ.update(env or {})
    try:
        with (
            redirect_stdout(out),
            redirect_stderr(err),
            patch.object(talent_kit, "claude_command", stub_command),
        ):
            code = talent_kit.main(argv)
    finally:
        for k, v in old.items():
            if v is None:
                talent_kit.os.environ.pop(k, None)
            else:
                talent_kit.os.environ[k] = v
    return code, out.getvalue() + err.getvalue()


def _rows(tmp: Path, sql: str):
    with closing(sqlite3.connect(tmp / "state.db")) as conn:
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
    def test_profile_without_company_stops_before_launching(self):
        with tempfile.TemporaryDirectory() as d:
            with (
                patch.object(talent_kit, "invoke") as invoke,
                self.assertRaises(SystemExit) as error,
            ):
                _run(
                    Path(d),
                    "02",
                    profile_text="# Profile\n\n## Organization\nname:  \n",
                )
            self.assertEqual(error.exception.code, 1)
            invoke.assert_not_called()

    def test_shared_profile_organization_name_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = _run(
                Path(d),
                "02",
                "--dry-run",
                profile_text="# Profile\n\n## Organization\nname: Example Robotics Co (stated by user)\n",
            )
            self.assertEqual(code, 0, out)

    def test_bulleted_or_bold_organization_name_is_accepted(self):
        """Setup wrote `- name: ...` lines and the runner used to refuse them."""
        for line in (
            "- name: Example Robotics Co (stated by user)",
            "* **Name:** Example Robotics Co (stated by user)",
            "**name**: Example Robotics Co",
        ):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as d:
                code, out = _run(
                    Path(d),
                    "02",
                    "--dry-run",
                    profile_text=f"# Profile\n\n## Organization\n{line}\n- domain: example.test\n",
                )
                self.assertEqual(code, 0, out)

    def test_bulleted_blank_name_still_stops(self):
        with tempfile.TemporaryDirectory() as d:
            with (
                patch.object(talent_kit, "invoke") as invoke,
                self.assertRaises(SystemExit) as error,
            ):
                _run(
                    Path(d),
                    "02",
                    profile_text="# Profile\n\n## Organization\n- name:   \n- domain: example.test\n",
                )
            self.assertEqual(error.exception.code, 1)
            invoke.assert_not_called()

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
        for final in ("BLOCKED", "123", "", "PASSIVE", "PASS but blocked"):
            with self.subTest(final=final):
                self.assertEqual(
                    talent_kit.last_verdict(
                        f"VERDICT: PASS\nVERDICT: {final}", ("PASS", "RETURNED")
                    ),
                    "UNKNOWN",
                )


class PackSnapshot(unittest.TestCase):
    def test_critic_reads_current_snapshot_on_first_run_and_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            original = talent_kit.invoke
            reviewed = []

            def invoke(ctx, agent, label, message):
                if label == "pack-critic":
                    snapshot = ctx["run_dir"] / "pack.json"
                    self.assertTrue(snapshot.is_file(), message)
                    self.assertIn(str(snapshot), message)
                    reviewed.append(json.loads(snapshot.read_text(encoding="utf-8")))
                return original(ctx, agent, label, message)

            with patch.object(talent_kit, "invoke", invoke):
                code, out = _run(tmp, "pack")
                self.assertEqual(code, 0, out)
                role_home = tmp / "talent-one-roles" / "controls-engineer"
                pack = json.loads((role_home / "pack.json").read_text(encoding="utf-8"))
                pack["role"]["company"] = ""
                (role_home / "pack.json").write_text(json.dumps(pack), encoding="utf-8")
                code, out = _run(tmp, "pack")
                self.assertEqual(code, talent_kit.GATE_FAILED, out)
            self.assertEqual(len(reviewed), 2)
            self.assertEqual(reviewed[1]["role"]["company"], "")

    def test_reused_pack_applies_current_operator_constraints(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            code, out = _run(tmp, "pack")
            self.assertEqual(code, 0, out)
            constraints = tmp / "constraints.json"
            constraints.write_text('["No travel"]', encoding="utf-8")
            code, out = _run(tmp, "pack", "--constraints-file", str(constraints))
            snapshot = (
                tmp / "talent-one-roles/controls-engineer/runs/2026-10-28/pack.json"
            )
            self.assertEqual(
                json.loads(snapshot.read_text())["constraints"], ["No travel"]
            )


class VerifyFreshness(unittest.TestCase):
    def test_failed_child_cannot_supply_a_passing_result(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = {
                "run_dir": Path(d),
                "role_home": Path(d),
                "model_override": {},
                "dry_run": False,
                "timeout": 10,
            }
            with (
                patch.object(
                    talent_kit, "agent_file", return_value=({"model": "fixture"}, "")
                ),
                patch.object(talent_kit, "agent_tools", return_value=[]),
                patch.object(talent_kit, "system_prompt", return_value="synthetic"),
                patch.object(talent_kit, "claude_command", return_value=["fixture"]),
                patch.object(
                    talent_kit.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess(
                        ["fixture"],
                        1,
                        '{"is_error": false, "result": "VERDICT: PASS"}',
                        "",
                    ),
                ),
                self.assertRaisesRegex(RuntimeError, "exited 1"),
            ):
                talent_kit.invoke(ctx, "critic", "fixture", "synthetic")

    def test_crashed_verify_cannot_reuse_old_passing_report(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "content").mkdir()
            (tmp / "content" / "02.content.json").write_text("{}", encoding="utf-8")
            (tmp / "verify").mkdir()
            (tmp / "verify" / "02.verify.json").write_text(
                '{"findings": [], "verdict": "PASS"}', encoding="utf-8"
            )
            ctx = {
                "manifest": talent_kit.load_manifest(),
                "run_dir": tmp,
                "run_id": "fixture",
                "slug": "fixture",
                "render_args": [],
                "dry_run": False,
            }

            def run_command(command, **kwargs):
                if command[2] == "render":
                    Path(command[command.index("--out") + 1]).write_text(
                        "<html></html>", encoding="utf-8"
                    )
                    return subprocess.CompletedProcess(command, 0, "", "")
                return subprocess.CompletedProcess(command, 1, "", "fixture crash")

            store = Mock()
            with patch.object(talent_kit.subprocess, "run", run_command):
                self.assertEqual(talent_kit.render_one(ctx, store, "02"), -1)
            store.save_artifact.assert_called_once_with(
                "fixture", "02", "jdbot", "verify-failed"
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
