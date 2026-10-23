"""Context budget for the Talent One module.

Reports three buckets (bytes/4 as the token estimate):
  (a) resident: skill descriptions plus the agent listings (description and tools line) a session holds
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

# Measured on the shipped 1.1.3 tree plus about three percent headroom (resident 2,578 with
# the agent listings counted; main window 3,410; largest bundle scout at 12,948 with
# baselines.json). Lower a ceiling when a cut lands; never raise one to make the check pass.
# On-demand references (ORCHESTRATOR_*.md, CONNECTOR_RUNTIME.md) load only on their path.
CEILINGS = {"resident": 2650, "main": 3500, "bundle_max": 13300}


def tok(path: str) -> int:
    try:
        return os.path.getsize(path) // 4
    except OSError:
        return 0


def _fm_fields(path: str) -> dict:
    with open(path, encoding="utf-8", errors="ignore") as fh:
        text = fh.read()
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    fields: dict = {}
    if not match:
        return fields
    key = None
    for line in match.group(1).split("\n"):
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def frontmatter_tok(path: str) -> int:
    """Tokens of what a session actually holds for this file.

    For a skill that is the `description:` text. For an agent it is the listing
    Claude Code renders into the main context, `- <name>: <description> (Tools: ...)`,
    where the Tools part is the agent's `tools:` line with any `disallowedTools`
    removed, or "All tools except ..." when no `tools:` line is set. Everything
    else in the frontmatter (model, color) is loader configuration."""
    f = _fm_fields(path)
    desc = f.get("description", "").strip().strip('"').strip("'")
    if "/agents/" not in path.replace(os.sep, "/"):
        return len(desc) // 4
    tools = [x.strip() for x in f.get("tools", "").split(",") if x.strip()]
    deny = [x.strip() for x in f.get("disallowedTools", "").split(",") if x.strip()]
    if tools:
        shown = ", ".join(x for x in tools if x not in deny)
    elif deny:
        shown = "All tools except " + ", ".join(deny)
    else:
        shown = "All tools"
    listing = f"- {f.get('name', '')}: {desc} (Tools: {shown})"
    return len(listing) // 4


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
