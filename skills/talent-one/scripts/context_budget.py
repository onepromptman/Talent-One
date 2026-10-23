"""Context budget for the Talent One module.

Reports three buckets (bytes/4 as the token estimate):
  (a) resident: skill + agent descriptions, present in every session the plugin is installed
  (b) main window: the orchestrator SKILL.md
  (c) per-subagent bundle: agents/<x>.md + references/briefs/<x>.md (+ example content when named)

`--check` exits nonzero when a bucket crosses its ceiling, so the numbers cannot drift back.
Run from the module root: python skills/talent-one/scripts/context_budget.py [--check]
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

# Measured on the shipped 1.1.0 tree plus two to four percent headroom (resident 1,841;
# main window 3,301; largest bundle scout at 12,748 with baselines.json). Lower a ceiling
# when a cut lands; never raise one to make the check pass. On-demand references
# (ORCHESTRATOR_*.md, CONNECTOR_RUNTIME.md) load only on their path and are not counted.
CEILINGS = {"resident": 1900, "main": 3400, "bundle_max": 13000}


def tok(path: str) -> int:
    try:
        return os.path.getsize(path) // 4
    except OSError:
        return 0


def frontmatter_tok(path: str) -> int:
    """Tokens of the `description:` field alone: that is what a session holds for every
    installed skill and agent. The rest of the frontmatter (tools, disallowedTools,
    model) is loader configuration and never enters the model's context."""
    with open(path, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return 0
    lines = match.group(1).split("\n")
    out: list[str] = []
    grab = False
    for line in lines:
        if re.match(r"^[A-Za-z][A-Za-z0-9_-]*:", line):
            grab = line.startswith("description:")
            if grab:
                out.append(line[len("description:"):].strip())
            continue
        if grab:
            out.append(line.strip())
    return len(" ".join(x for x in out if x)) // 4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = args.root
    base = os.path.join(root, "skills", "talent-one")

    skills = glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))
    agents = sorted(glob.glob(os.path.join(root, "agents", "*.md")))
    resident = sum(frontmatter_tok(p) for p in skills) + sum(frontmatter_tok(p) for p in agents)
    main_window = tok(os.path.join(base, "SKILL.md"))

    # The brief states it replaces the four reference files and the example content, so the
    # bundle is agent + brief (+ baselines for scout). Pack, research file and profile are
    # per-role inputs and are reported from the eval fixture when present.
    pack = tok(os.path.join(root, "evals", "fixtures", "pack.json"))
    baselines = os.path.join(base, "references", "baselines.json")
    rows = []
    for agent in agents:
        name = os.path.basename(agent)[:-3]
        brief = os.path.join(base, "references", "briefs", f"{name}.md")
        extra = tok(baselines) if name == "scout" else 0
        rows.append((name, tok(agent), tok(brief), extra))

    print(f"(a) resident every session: {resident} tok ({len(skills)} skills, {len(agents)} agents)")
    print(f"(b) main window per run:    {main_window} tok")
    print(f"(c) per-subagent bundle (agent + brief [+ baselines]); pack fixture adds {pack} tok each:")
    total = 0
    worst = 0
    for name, a, b, e in rows:
        bundle = a + b + e
        total += bundle
        worst = max(worst, bundle)
        print(f"    {name:18} agent {a:5}  brief {b:5}  extra {e:5}  bundle {bundle:6}")
    print(f"    single fan-out: {total} tok of instruction before any work")
    print("    (repair laps and the QA gate add to this on a real run)")

    if not args.check:
        return 0
    failures = []
    if resident > CEILINGS["resident"]:
        failures.append(f"resident {resident} > {CEILINGS['resident']}")
    if main_window > CEILINGS["main"]:
        failures.append(f"main window {main_window} > {CEILINGS['main']}")
    if worst > CEILINGS["bundle_max"]:
        failures.append(f"largest bundle {worst} > {CEILINGS['bundle_max']}")
    for failure in failures:
        print("FAIL:", failure, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
