"""The renderer runs on a bare Python: no pip install, no site-packages.

`python -S` starts Python without its site-packages folder, so the only bs4 the renderer
can import is the copy bundled in `skills/talent-one/scripts/_vendor/`. Run from the module
directory (or the Talent One repository root): `python -m pytest -q tests`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent / "skills" / "talent-one"
RENDER = SKILL_ROOT / "scripts" / "render.py"
REF = SKILL_ROOT / "references"


def _bare(*args: str) -> subprocess.CompletedProcess:
    # -S: no site-packages; -s: no user site; -E: ignore PYTHON* variables.
    return subprocess.run(
        [sys.executable, "-S", "-s", "-E", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_bare_python_has_no_bs4_of_its_own():
    probe = _bare("-c", "import importlib.util as u; print(u.find_spec('bs4') is None)")
    assert probe.stdout.strip() == "True", probe.stdout + probe.stderr


def test_render_works_with_no_packages(tmp_path):
    out = tmp_path / "TK_08.html"
    proc = _bare(
        str(RENDER),
        "render",
        "--template",
        str(REF / "templates" / "TK_08_Recruiter_Screen.dc.html"),
        "--schema",
        str(REF / "content-schemas" / "TK_08.content-schema.json"),
        "--content",
        str(REF / "content-schemas" / "TK_08.example-content.json"),
        "--ds",
        str(REF / "templates" / "_ds" / "onepromptman-ds"),
        "--out",
        str(out),
        "--strict",
        "--mode",
        "light",
        "--prefix",
        "TK",
        "--credit",
        "on",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "soupsieve" not in proc.stderr
    assert out.is_file() and out.stat().st_size > 1000
