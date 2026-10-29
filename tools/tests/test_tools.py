"""Tests for the maintainer tools: check_dag.py, check_fill.py, check_kit.sh and
extract_slot_schema.py. They assert structure (wiring, slot and repeat names, bar
geometry, script behaviour), never the worked example's wording, so a re-skinned
example or a renamed token set keeps them green.

Stdlib unittest, collected by pytest when the module's evals run. The rendered-run test
shells out to skills/talent-one/scripts/render.py (beautifulsoup4).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
MODULE = TOOLS.parent
REF = MODULE / "skills" / "talent-one" / "references"
TEMPLATES = REF / "templates"
SCHEMAS = REF / "content-schemas"
RENDER = MODULE / "skills" / "talent-one" / "scripts" / "render.py"
sys.path.insert(0, str(TOOLS))
import check_dag
import check_fill
import extract_slot_schema

# /bin/bash is 3.2 on macOS: the version check_kit.sh's empty-array fix is for.
BASH = "/bin/bash" if Path("/bin/bash").exists() else shutil.which("bash")


def _lint(html: str, *extra: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "01_x.html"
        f.write_text(html, encoding="utf-8")
        out = io.StringIO()
        old = sys.argv
        sys.argv = ["check_fill.py", str(f), "--no-schema", *extra]
        try:
            with redirect_stdout(out):
                code = check_fill.main()
        finally:
            sys.argv = old
        return code, out.getvalue()


HANDOFF = (
    '<p data-slot="handoff.produces">a · b</p>'
    '<p data-slot="handoff.blocked">Nothing</p>'
)


class CheckDag(unittest.TestCase):
    def test_module_wiring_agrees(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = check_dag.main()
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("0 inter-artifact edges", out.getvalue())

    def test_drift_in_the_runner_manifest_is_caught(self):
        manifest = json.loads(check_dag.MANIFEST.read_text(encoding="utf-8"))
        manifest["artifacts"]["02"]["pack_paths"] = manifest["artifacts"]["02"][
            "pack_paths"
        ][:-1]
        manifest["artifacts"]["06"]["agent"] = "jdbot"
        with tempfile.TemporaryDirectory() as d:
            alt = Path(d) / "agents.json"
            alt.write_text(json.dumps(manifest), encoding="utf-8")
            orig = check_dag.MANIFEST
            check_dag.MANIFEST = alt
            out = io.StringIO()
            try:
                with redirect_stdout(out):
                    code = check_dag.main()
            finally:
                check_dag.MANIFEST = orig
        self.assertEqual(code, 1)
        self.assertIn("02: runner pack_paths", out.getvalue())
        self.assertIn("06: runner says 'jdbot'", out.getvalue())

    def test_section5_parses_research_paths(self):
        rows = check_dag.section5(check_dag.CONTEXT_PACK.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 9)
        self.assertTrue(any(p.startswith("research:") for p in rows["03"]["required"]))


class CheckFill(unittest.TestCase):
    def test_understated_bar_is_an_error(self):
        code, out = _lint(f'<div data-bar="0.6" style="width:40%"></div>{HANDOFF}')
        self.assertEqual(code, 1, out)
        self.assertIn("understates", out)

    def test_range_bar_geometry(self):
        ok, _ = _lint(
            f'<div data-bar="0.2,0.5" style="left:20%;width:30%"></div>{HANDOFF}'
        )
        bad, out = _lint(
            f'<div data-bar="0.2,0.5" style="left:20%;width:10%"></div>{HANDOFF}'
        )
        self.assertEqual((ok, bad), (0, 1), out)

    def test_heat_cell_accepts_any_primary_token_prefix(self):
        for token in ("--ds-primary", "--op-primary"):
            code, out = _lint(
                f'<div data-bar="1" style="background:var({token});'
                f'min-height:40px"></div>{HANDOFF}'
            )
            self.assertEqual(code, 0, out)
        code, out = _lint(
            f'<div data-bar="1" style="background:#DCE6F2;min-height:40px">'
            f"</div>{HANDOFF}"
        )
        self.assertEqual(code, 1, out)

    def test_hedged_optional_block_is_an_error(self):
        code, out = _lint(f"<div data-optional>Comp data TBD</div>{HANDOFF}")
        self.assertEqual(code, 1)
        self.assertIn("hedged-optional", out)

    def test_inlined_css_is_not_body_text(self):
        _code, out = _lint(
            f"<style>/* tokens — header */</style><p>fine text</p>{HANDOFF}"
        )
        self.assertNotIn("em-dash", out)
        _code, out = _lint(f"<p>bad — text</p>{HANDOFF}")
        self.assertIn("em-dash", out)

    def test_handoff_keys_against_the_renderers_compat_file(self):
        with tempfile.TemporaryDirectory() as d:
            h = Path(d) / "handoffs.json"
            h.write_text(
                json.dumps({"01": {"handoff": {"produces": "a · b"}}}), encoding="utf-8"
            )
            ok, out = _lint(HANDOFF, "--handoffs", str(h), "--artifact", "01")
            self.assertEqual(ok, 0, out)
            h.write_text(
                json.dumps({"01": {"handoff": {"a": 1, "c": 2}}}), encoding="utf-8"
            )
            bad, out = _lint(HANDOFF, "--handoffs", str(h), "--artifact", "01")
            self.assertEqual(bad, 1, out)


class CheckKit(unittest.TestCase):
    def _kit(self, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, PYTHON=sys.executable)
        return subprocess.run(
            [BASH, str(TOOLS / "check_kit.sh"), *args],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_shipped_templates_on_the_system_bash(self):
        proc = self._kit()
        out = proc.stdout + proc.stderr
        self.assertNotIn("unbound variable", out)
        n = len(list(TEMPLATES.glob("TK_*.dc.html")))
        self.assertEqual(out.count("\n=== TK_"), n, out)
        self.assertIn(f"({n} file(s))", out)

    def test_a_rendered_run_folder(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            ds = next(p for p in (TEMPLATES / "_ds").iterdir() if p.is_dir())
            for nn, agent in (("02", "jdbot"), ("06", "interview-lab")):
                tpl = next(TEMPLATES.glob(f"TK_{nn}_*.dc.html"))
                subprocess.run(
                    [
                        sys.executable,
                        str(RENDER),
                        "render",
                        "--template",
                        str(tpl),
                        "--schema",
                        str(SCHEMAS / f"TK_{nn}.content-schema.json"),
                        "--content",
                        str(SCHEMAS / f"TK_{nn}.example-content.json"),
                        "--ds",
                        str(ds),
                        "--out",
                        str(run / f"{nn}_{agent}.html"),
                        "--handoffs",
                        str(run / "handoffs.json"),
                        "--role",
                        "test-role",
                        "--strict",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            proc = self._kit(str(run))
            out = proc.stdout + proc.stderr
            self.assertNotIn("unbound variable", out)
            self.assertIn("(2 file(s))", out)
            # The worked example renders against itself, so unfilled-slot errors are
            # expected; geometry, colour, handoff and voice errors are not.
            self.assertIn("ERROR unfilled-slot", out)  # the report format this reads
            for check in (
                "bar-geometry",
                "raw-hex",
                "handoff",
                "em-dash",
                "forbidden-phrase",
                "empty-repeat",
            ):
                self.assertNotIn(f"ERROR {check} ", out)

    def test_empty_folder_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self._kit(d)
            self.assertEqual(proc.returncode, 2)


class ExtractSlotSchema(unittest.TestCase):
    def test_check_is_clean_for_a_matching_schema_and_names_drift(self):
        slots, repeats = extract_slot_schema.infer()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "SLOT_SCHEMA.json"
            doc = {"types": {}, "slots": slots, "repeats": repeats}
            p.write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(extract_slot_schema.check(p), [])
            gone = min(slots)
            del doc["slots"][gone]
            doc["repeats"]["not-a-repeat"] = {"count": "1", "templates": ["TK_01"]}
            p.write_text(json.dumps(doc), encoding="utf-8")
            drift = extract_slot_schema.check(p)
            self.assertTrue(any(gone in line for line in drift), drift)
            self.assertTrue(any("not-a-repeat" in line for line in drift), drift)

    def test_every_type_has_a_linter_pattern(self):
        known = set(check_fill.TYPE_PATTERNS) | check_fill.FREE_TEXT_TYPES | {"chip"}
        emitted = {name for name, _ in extract_slot_schema.PATTERNS}
        self.assertLessEqual(emitted, known)
        committed = json.loads((REF / "SLOT_SCHEMA.json").read_text(encoding="utf-8"))
        used = {s.get("type") for s in committed["slots"].values()}
        self.assertLessEqual(used, known, used - known)


if __name__ == "__main__":
    unittest.main()
