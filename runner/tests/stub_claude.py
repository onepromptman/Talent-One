#!/usr/bin/env python3
"""A stand-in for `claude -p` used by the runner tests. Never calls a model.

It reads the same arguments and stdin the runner sends, works out which session it is
from the system-prompt file name the runner writes (<label>.system.md), and does what
that agent would do, deterministically:
  pack-scout     writes a synthetic pack.json + pack-research.json into the role home
                 (the module's eval fixture pack plus synthetic values for the paths it
                 lacks; STUB_PACK_MINIMAL=1 writes the fixture pack alone)
  content-NN-*   copies the shipped TK_NN.example-content.json to the requested path
  pack-critic, critic-NN   answers `VERDICT: PASS` (STUB_CRITIC=RETURNED to refuse)
  qa             answers `VERDICT: CERTIFIED`
It prints the JSON envelope `claude -p --output-format json` prints. STUB_SLEEP holds
each session open so parallel sessions overlap.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2]
SCHEMAS = MODULE / "skills" / "talent-one" / "references" / "content-schemas"
FIXTURE_PACK = MODULE / "evals" / "fixtures" / "pack.json"


def arg(flag):
    argv = sys.argv[1:]
    return argv[argv.index(flag) + 1] if flag in argv else None


def line_value(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def main():
    user = sys.stdin.read()
    label = Path(arg("--append-system-prompt-file")).name.replace(".system.md", "")
    time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
    result = f"stub session {label}"
    if label == "pack-scout":
        home = Path(line_value(user, "role home:"))
        pack = json.loads(FIXTURE_PACK.read_text(encoding="utf-8"))
        pack.pop("constraints", None)
        research = {}
        if os.environ.get("STUB_PACK_MINIMAL") != "1":
            synth = {"value": "synthetic", "pill": "Estimate", "method": "test stub"}
            pack.setdefault("timing", {})["sla"] = synth
            pack["targets"] = {"tier1": [synth], "geo_sequence": [synth]}
            pack["personas"] = [{"name": "synthetic persona"}]
            pack["channels"] = [{"name": "synthetic channel"}]
            pack.setdefault("market", {}).setdefault("funnel", synth)
            pack.setdefault("comp", {}).setdefault("by_level", [synth])
            research = {k: [{"name": "synthetic"}] for k in
                        ("dossiers", "metros", "persona_detail", "proof_points")}
            research["quadrant"] = [{"name": "synthetic", "x": 0.5, "y": 0.5, "size": 0.5,
                                     "tier": "A"}]
        (home / "pack.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
        if research:
            (home / "pack-research.json").write_text(json.dumps(research), encoding="utf-8")
    elif label.startswith("content-"):
        nn = label.split("-")[1]
        out = Path(line_value(user, "WRITE YOUR CONTENT JSON TO:"))
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SCHEMAS / f"TK_{nn}.example-content.json", out)
        result = f"wrote {out}"
    elif label.startswith("critic-") or label == "pack-critic":
        result += "\nVERDICT: " + os.environ.get("STUB_CRITIC", "PASS")
    elif label == "qa":
        result += "\nVERDICT: CERTIFIED"
    print(json.dumps({"result": result, "session_id": f"stub-{label}",
                      "total_cost_usd": 0.01, "is_error": False}))


if __name__ == "__main__":
    main()
