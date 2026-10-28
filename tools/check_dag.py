#!/usr/bin/env python3
"""Talent One wiring check: the 2.x phase shape, stated in five places, must agree.

In 2.x there is no inter-artifact DAG left: the Context Pack carries every
cross-artifact decision, all nine artifact agents run in parallel against it, and the
phases are fixed (pack, content, critic, render, qa). That shape is stated in:

  skills/talent-one/references/CONTEXT_PACK.md  section 5: each artifact's required
                                                pack paths (the preflight keys)
  runner/agents.json                            the headless runner's phase manifest
  MODULE.yaml                                   agent roles and verifiers
  skills/talent-one/scripts/render.py           AGENT_BY_ARTIFACT (artifact -> agent)
  agents/relay.md                               the in-session orchestrator's phases

plus the per-artifact files (template, content schema, worked example, agent file,
precompiled brief). Drift between them is silent and expensive: a runner that
preflights a path the reference no longer requires, an artifact with no renderer
binding, or an edge between two artifacts that were supposed to be independent.

    python3 tools/check_dag.py            # from the module directory or anywhere

Exit 0 when everything agrees, 1 with one FAIL line per disagreement. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent
REF = MODULE / "skills" / "talent-one" / "references"
CONTEXT_PACK = REF / "CONTEXT_PACK.md"
RENDER = MODULE / "skills" / "talent-one" / "scripts" / "render.py"
MANIFEST = MODULE / "runner" / "agents.json"
MODULE_YAML = MODULE / "MODULE.yaml"
RELAY = MODULE / "agents" / "relay.md"

PHASES = ["pack", "content", "critic", "render", "qa"]
# The relay's own phase headings, in order, as agents/relay.md writes them.
RELAY_MARKERS = ["**Phase 1 (pack).**", "**Phase 2 (content", "**Phase 2.5 (critic",
                 "**Phase 3 (render", "**Phase 4 (qa-gate"]


def norm(name: str) -> str:
    """`JD-BOT`, `jdbot` and `Jd Bot` all compare equal; so do `INTERVIEW LAB` and
    `interview-lab`."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def section5(text: str) -> dict[str, dict]:
    """artifact -> {agent, required:[paths], optional:[paths], raw:str} from the
    CONTEXT_PACK.md section 5 table."""
    m = re.search(r"^## 5\..*?$(.*?)^## ", text, re.M | re.S)
    if not m:
        raise SystemExit("FAIL  CONTEXT_PACK.md has no section 5")
    rows = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not re.match(r"^\d{2} [a-z-]+$", cells[0]):
            continue
        nn, agent = cells[0].split(" ", 1)
        main, _, research = cells[1].partition("+ research:")
        required = [p.strip() for p in main.split(",") if p.strip()]
        required += [f"research:{p.strip()}" for p in research.split(",") if p.strip()]
        optional = [p.strip() for p in cells[2].split(",") if p.strip()]
        rows[nn] = {"agent": agent, "required": required, "optional": optional,
                    "raw": cells[1] + " " + cells[2]}
    return rows


def module_agents(text: str) -> dict[str, dict]:
    """name -> {role, verifier} from MODULE.yaml's `agents:` block (flow mappings)."""
    m = re.search(r"^agents:\n((?:[ \t]+.*\n|\n)+)", text, re.M)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        a = re.match(r"^\s+([a-z0-9-]+):\s*\{(.*)\}\s*$", line)
        if not a:
            continue
        fields = dict(
            (k.strip(), v.strip())
            for k, _, v in (kv.partition(":") for kv in a.group(2).split(","))
        )
        out[a.group(1)] = fields
    return out


def renderer_agents(text: str) -> dict[str, str]:
    m = re.search(r"AGENT_BY_ARTIFACT\s*=\s*\{(.*?)\}", text, re.S)
    return dict(re.findall(r'"(\d{2})"\s*:\s*"([^"]+)"', m.group(1))) if m else {}


def main() -> int:
    fails: list[str] = []

    def fail(msg: str):
        fails.append(msg)
        print(f"FAIL  {msg}")

    for p in (CONTEXT_PACK, RENDER, MANIFEST, MODULE_YAML, RELAY):
        if not p.is_file():
            fail(f"missing {p.relative_to(MODULE)}")
    if fails:
        return 1

    rows = section5(CONTEXT_PACK.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    agents = module_agents(MODULE_YAML.read_text(encoding="utf-8"))
    by_art = renderer_agents(RENDER.read_text(encoding="utf-8"))
    relay = RELAY.read_text(encoding="utf-8")
    arts = manifest.get("artifacts", {})

    # 1. One artifact set everywhere.
    sets = {"CONTEXT_PACK.md section 5": set(rows), "runner/agents.json": set(arts),
            "render.py AGENT_BY_ARTIFACT": set(by_art)}
    ref = set(rows)
    for where, got in sets.items():
        if got != ref:
            fail(f"{where} artifacts {sorted(got)} != section 5 {sorted(ref)}")

    # 2. The same agent per artifact, a real executor checked by critic, with its files.
    for nn in sorted(ref):
        agent = rows[nn]["agent"]
        if nn in arts and arts[nn].get("agent") != agent:
            fail(f"{nn}: runner says {arts[nn].get('agent')!r}, section 5 says {agent!r}")
        if nn in by_art and norm(by_art[nn]) != norm(agent):
            fail(f"{nn}: render.py says {by_art[nn]!r}, section 5 says {agent!r}")
        spec = agents.get(agent)
        if spec is None:
            fail(f"{nn}: agent {agent!r} is not declared in MODULE.yaml")
        elif spec.get("role") != "executor" or spec.get("verifier") != manifest.get(
                "critic_agent"):
            fail(f"{nn}: {agent} is {spec}, expected an executor verified by "
                 f"{manifest.get('critic_agent')}")
        for path in (MODULE / "agents" / f"{agent}.md",
                     REF / "briefs" / f"{agent}.md",
                     REF / "content-schemas" / f"TK_{nn}.content-schema.json",
                     REF / "content-schemas" / f"TK_{nn}.example-content.json"):
            if not path.is_file():
                fail(f"{nn}: missing {path.relative_to(MODULE)}")
        if len(list((REF / "templates").glob(f"TK_{nn}_*.dc.html"))) != 1:
            fail(f"{nn}: expected exactly one templates/TK_{nn}_*.dc.html")

    # 3. The runner preflights exactly the reference's required paths.
    for nn in sorted(ref & set(arts)):
        a, b = sorted(arts[nn].get("pack_paths", [])), sorted(rows[nn]["required"])
        if a != b:
            fail(f"{nn}: runner pack_paths {a} != section 5 required {b}")

    # 4. No inter-artifact edge: a section 5 row names pack paths, never an artifact.
    names = {norm(r["agent"]) for r in rows.values()}
    edges = 0
    for nn, row in sorted(rows.items()):
        refs = set(re.findall(r"\bA0\d\b|\b0[1-9]\b", row["raw"]))
        refs |= {w for w in re.findall(r"[a-z][a-z-]+", row["raw"]) if norm(w) in names}
        if refs:
            edges += len(refs)
            fail(f"{nn}: section 5 row references other artifacts {sorted(refs)}; "
                 "cross-artifact values belong in the pack")

    # 5. The fixed phases: the runner's manifest, the relay's headings, the verifiers.
    if manifest.get("phases") != PHASES:
        fail(f"runner phases {manifest.get('phases')} != {PHASES}")
    pos = [relay.find(m) for m in RELAY_MARKERS]
    if -1 in pos or pos != sorted(pos):
        missing = [m for m, i in zip(RELAY_MARKERS, pos) if i == -1]
        fail(f"agents/relay.md phase headings missing or out of order: {missing or pos}")
    for key, role in (("pack_agent", "executor"), ("critic_agent", "verifier"),
                      ("qa_agent", "verifier")):
        name = manifest.get(key)
        if agents.get(name, {}).get("role") != role:
            fail(f"runner {key} {name!r} is not a {role} in MODULE.yaml")
        elif not (MODULE / "agents" / f"{name}.md").is_file():
            fail(f"runner {key} {name!r} has no agents/{name}.md")

    if fails:
        return 1
    print(f"wiring: {len(ref)} artifacts, {edges} inter-artifact edges; phases "
          f"{' -> '.join(PHASES)}.")
    print("CONTEXT_PACK.md section 5, runner/agents.json, MODULE.yaml, render.py and "
          "agents/relay.md agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
