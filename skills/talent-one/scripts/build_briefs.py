#!/usr/bin/env python3
"""
build_briefs.py  ·  Fix F2 (agent context-cost, HIGH/speed)

PROBLEM THIS SOLVES
--------------------
Every Talent One agent's RUNTIME block used to say "read these four things":
00_SHARED_CORE.md (~19KB), the CONTEXT_PACK.md §5 table (which meant opening
the whole ~15KB file), its block in 02_GROUNDING_MATRIX.md (which meant
opening the whole ~24KB file), and its own content-schema.json plus
example-content.json pair (~18-40KB combined). Most of each file is
irrelevant to any single agent. Measured cost: hunter alone spent 24.5
minutes on one spawn, much of it ingesting references it barely used.

THE FIX
-------
This is a BUILD-TIME script. It parses the four source reference files once,
slices out exactly what each agent needs per the mapping tables below, and
writes one precompiled brief per agent to references/briefs/<agent>.md
(target ~15KB, soft target 20KB, HARD ceiling 24KB — the script exits nonzero
when any brief crosses the hard ceiling, in --check mode too: a brief that
outgrows its budget is a build failure, not a warning to scroll past; trim the
source mapping, don't raise the ceiling). Each agent's RUNTIME block is edited (by
hand, not by this script) to read ONLY its brief, plus whatever is genuinely
unique to that agent and cannot be folded into a brief (scout's
baselines.json is the one example in this kit).

DESIGN
------
- Deterministic and idempotent. Same source files in, byte-identical briefs
  out, every run. No network calls, no LLM calls, no randomness. Diffing two
  runs against the same sources is always empty.
- Section-marker driven. Extraction keys off markdown headings (## N. TITLE,
  ### A0N NAME -> `TK_NN`, | table | rows |) rather than hardcoded byte
  offsets or copy-pasted prose, so a wording tweak in a source file does not
  silently break extraction the way a line-number or verbatim-string match
  would. A HEADING SHAPE CHANGE (a whole section renamed or restructured)
  will surface as a loud KeyError/assertion at build time, which is the
  correct failure mode: fail the build, don't ship a silently-wrong brief.
- All agent-to-content editorial judgment lives in the mapping tables in the
  EDITABLE MAPPING TABLES block below. Nothing else in this file should need
  to change when an agent's needs shift; only the tables should.
- Briefs are GENERATED ARTIFACTS. Never hand-edit references/briefs/*.md;
  re-run this script instead (it is safe to run any time any source file
  changes, and safe to run when nothing changed: output is unchanged).

USAGE
-----
    python3 build_briefs.py            # (re)generate every brief
    python3 build_briefs.py --check    # exit 1 if any brief would change
                                        # (wire into CI / pre-commit)

INPUTS READ (never modified by this script)
--------------------------------------------
    references/00_SHARED_CORE.md
    references/02_GROUNDING_MATRIX.md
    references/CONTEXT_PACK.md
    references/content-schemas/TK_NN.content-schema.json

OUTPUT
------
    references/briefs/<agent>.md   one per key in AGENT_CODE plus scout/relay
"""

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.normpath(os.path.join(HERE, "..", "references"))
BRIEFS_DIR = os.path.join(REF, "briefs")

# Soft target is 20KB (warn); crossing this hard ceiling fails the build,
# --check included. Trim the source mapping rather than raising it.
HARD_CEILING_BYTES = 24 * 1024

SHARED_CORE_PATH = os.path.join(REF, "00_SHARED_CORE.md")
GROUNDING_PATH = os.path.join(REF, "02_GROUNDING_MATRIX.md")
CONTEXT_PACK_PATH = os.path.join(REF, "CONTEXT_PACK.md")
SCHEMA_DIR = os.path.join(REF, "content-schemas")

SOURCE_FILES = [SHARED_CORE_PATH, GROUNDING_PATH, CONTEXT_PACK_PATH]

GENERATOR_NAME = "skills/talent-one/scripts/build_briefs.py"

# ============================================================================
# EDITABLE MAPPING TABLES
# This is the only block that should need to change when an agent's needs
# shift. Everything below it is generic extraction machinery driven by
# markdown headings in the three source files plus these tables.
# ============================================================================

# All 11 agents this kit ships.
ALL_AGENTS = [
    "sensei", "jdbot", "atlas", "hunter", "shakespeare", "interview-lab",
    "calibrate", "recruiter-screen", "qa-gate", "scout", "relay",
]

# Agent id (matches agents/<id>.md) -> its "### A0N NAME -> `TK_NN`" heading
# in 02_GROUNDING_MATRIX.md Part 3, and its Producer label in Part 3.5 /
# its Agent label in Part 4's per-agent fallback table (all three use the
# same "A0N NAME" string).
AGENT_CODE = {
    "sensei":            "A01 SENSEI",
    "jdbot":             "A02 JD-BOT",
    "atlas":             "A03 ATLAS",
    "hunter":            "A04 HUNTER",
    "shakespeare":       "A05 SHAKESPEARE",
    "interview-lab":     "A06 INTERVIEW LAB",
    "calibrate":         "A07 CALIBRATE",
    "recruiter-screen":  "A08 RECRUITER SCREEN",
    "qa-gate":           "A09 QA GATE",
}

# scout has no single Part 3 block of its own: scout.md's own GROUNDING
# section says "Your sources are the union of the A07 + A01 + A03 blocks."
SCOUT_SOURCE_AGENTS = ["A07 CALIBRATE", "A01 SENSEI", "A03 ATLAS"]

# Agent id -> bound content schema stem in references/content-schemas/.
# Agents absent from this dict (scout, qa-gate, relay) have no single bound
# template; see build_scout_brief / build_qa_gate_brief / build_relay_brief.
AGENT_SCHEMA = {
    "sensei": "TK_01", "jdbot": "TK_02", "atlas": "TK_03", "hunter": "TK_04",
    "shakespeare": "TK_05", "interview-lab": "TK_06", "calibrate": "TK_07",
    "recruiter-screen": "TK_08",
}

# Agent id -> its row label in CONTEXT_PACK.md §5's per-artifact table.
AGENT_PACK_ROW = {
    "sensei": "01 sensei", "jdbot": "02 jdbot", "atlas": "03 atlas",
    "hunter": "04 hunter", "shakespeare": "05 shakespeare",
    "interview-lab": "06 interview-lab", "calibrate": "07 calibrate",
    "recruiter-screen": "08 recruiter-screen",
}

# Top-level pack.json keys that legitimately exist (used to sanity-filter
# tokens parsed out of CONTEXT_PACK.md §5's "Required/Optional pack paths"
# cells: some cells use dotted paths like "spec.requirements", some use bare
# top-level keys like "personas". A stray bare token that matches neither
# form, e.g. a nested field name written without its parent key, is dropped
# rather than mis-extracted; see FIDELITY NOTES in the generated relay/scout
# briefs and the run report for the one case this kit's source file hits.
VALID_PACK_TOP_KEYS = {
    "pack_version", "role", "built", "built_from", "spec", "market", "comp",
    "keywords", "personas", "channels", "targets", "messaging", "timing",
    "constraints", "caveats", "assumptions", "freshness",
}
VALID_RESEARCH_TOP_KEYS = {
    "dossiers", "metros", "demand_blocs", "persona_detail", "proof_points",
    "quadrant", "pack_version", "role_slug", "built",
}

# Manual overrides: dotted pack.json paths an agent's own file (agents/*.md
# body, untouched by this fix) demonstrably reads, that CONTEXT_PACK.md §5
# does not list for that artifact. Each entry is a known, checked source-file
# gap (see the fidelity check in the F2 run report), not a guess: jdbot.md's
# METHOD section reads `market.classification` and calibrates a whole table
# against ABUNDANT/BALANCED/TIGHT/SCARCE, but the 02 jdbot row in
# CONTEXT_PACK.md §5 lists no `market.*` path at all, required or optional.
# hunter.md's TITLE SYNONYMS & KEYWORD TAXONOMY section reads
# `spec.must_have_skills`, `spec.nice_to_have`, `spec.education`, and
# `spec.years_experience` by name ("Core titles and skill keywords come from
# the pack's spec.must_have_skills, spec.nice_to_have, spec.education, and
# spec.years_experience: they set the AND-terms and the seniority band."),
# but the 04 hunter row in CONTEXT_PACK.md §5 lists no `spec.*` path at all,
# required or optional.
EXTRA_PACK_PATHS = {
    "jdbot": ["market.classification"],
    "hunter": ["spec.must_have_skills", "spec.nice_to_have",
               "spec.education", "spec.years_experience"],
}

# Agents whose bound artifact also reads pack-research.json (CONTEXT_PACK.md
# §5's "+ research: ..." suffix); the research top-level keys they need are
# derived from that suffix automatically, this list only gates whether the
# pack-research.json pv shape note is worth including at all.
RESEARCH_READERS = {"atlas", "hunter", "shakespeare"}

# Agent id -> 00_SHARED_CORE.md section codes to include verbatim, in
# document order. "3" (provenance) and "6.5" (the NEED_INPUT halt contract)
# are non-negotiable per the F2 brief: every agent that reads any shared
# core at all gets them. "5" (content contract) is agent-specific by
# construction: trim_content_contract() below replaces its all-9-agents
# table with a one- or two-line pointer scoped to THIS agent before the
# section is emitted, so listing "5" here does not mean the agent inherits
# every other agent's schema filename.
SHARED_CORE_SECTIONS = {
    # Every agent's own RUNTIME preamble (agents/*.md, NOT edited by this
    # script beyond the "read these files" line) already restates §1's two
    # substantive rules verbatim ("Company/org values come from the profile
    # ..., never hardcoded, never invented"), so §1 IDENTITY is dropped
    # everywhere: it is boilerplate the agent file already carries.
    #
    # The 8 artifact-producing agents: everything else in shared core
    # governs something they do.
    "sensei":            ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "jdbot":             ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "atlas":             ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "hunter":            ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "shakespeare":       ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "interview-lab":     ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "calibrate":         ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    "recruiter-screen":  ["1.5", "2", "3", "4", "5", "6", "6.5", "7"],
    # scout writes the pack, not a content JSON: no §5 (content-JSON
    # contract), no §6 (the handoff object it never emits), no §7
    # (self-QA is content-JSON specific; scout's own OUTPUT CONTRACT step
    # "validate-pack" is its equivalent and lives in scout.md, untouched).
    "scout":             ["1.5", "2", "3", "4", "6.5"],
    # qa-gate audits every other agent's compliance with all of shared core,
    # so it needs the substantive rule sections including the content
    # contract and self-QA checklist it audits against. It has its own
    # missing-content fallback (not the NEED_INPUT block) and no preflight
    # of its own, so 1.5 and 6.5 are dropped to leave room for its (large)
    # grounding-matrix and pack-fidelity slice.
    "qa-gate":           ["2", "3", "4", "5", "6", "7"],
    # relay is a pure planner: it never writes provenance, pills, content,
    # or a handoff, and never halts via NEED_INPUT. No shared-core slice.
    "relay":              [],
}

# ============================================================================
# GENERIC EXTRACTION MACHINERY (should not need editing per agent)
# ============================================================================


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def split_sections(text, level=2):
    """Split text on '#'*level + ' ' + heading, returning
    {short_code_or_heading: full_section_text_including_heading}, in order.
    short_code is the leading "N" or "N.M" digits of the heading when the
    heading starts with one (00_SHARED_CORE.md, CONTEXT_PACK.md); otherwise
    the full heading text is the key (02_GROUNDING_MATRIX.md's "PART n ..."
    headings)."""
    marker = "#" * level + " "
    pattern = re.compile(rf"(?m)^{re.escape(marker)}(.+)$")
    matches = list(pattern.finditer(text))
    sections, order = {}, []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        codem = re.match(r"([\d.]+)", heading)
        code = codem.group(1).rstrip(".") if codem else heading
        sections[code] = body
        order.append(code)
    return sections, order


def parse_md_table(text):
    """First pipe-table in text -> list of {header: cell} dicts."""
    lines = text.splitlines()
    tbl_lines = [l for l in lines if l.strip().startswith("|")]
    if len(tbl_lines) < 2:
        return []
    header = [c.strip() for c in tbl_lines[0].strip("|").split("|")]
    rows = []
    for l in tbl_lines[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def extract_fenced_json(section_text, n=0):
    """n-th ```json ... ``` fence body inside section_text, or None."""
    fences = list(re.finditer(r"```json\n(.*?)```", section_text, re.S))
    if not fences:
        return None
    return fences[n].group(1)


def extract_key_block(fence, key, indent=2):
    """Bracket-depth extraction of one top-level '  "key": {...}' or
    '  "key": [...]' or '  "key": "scalar"' block from a JSON-shaped (not
    necessarily valid-JSON, may carry // comments) fenced code block. Returns
    the raw text (comments intact) or None if key is absent. Deterministic
    text scan, not a JSON parser: this file's example blocks carry // (req)
    annotations that are useful for a reading agent and are not valid JSON,
    so we never json.loads() them."""
    pat = re.compile(rf'(?m)^{" " * indent}"{re.escape(key)}":\s*')
    m = pat.search(fence)
    if m is None:
        # Fallback: some source lines pack more than one sibling field per
        # line (e.g. `"must_have_skills": ["..."], "nice_to_have": ["..."],`)
        # so the second field never starts a line and the anchored pattern
        # above misses it. Match the quoted key anywhere instead; the quotes
        # already guarantee an exact key match, not a substring hit.
        m = re.search(rf'"{re.escape(key)}":\s*', fence)
        if m is None:
            return None
    i = m.end()
    if i < len(fence) and fence[i] in "{[":
        open_c, close_c = fence[i], ("}" if fence[i] == "{" else "]")
        depth, j = 0, i
        while j < len(fence):
            if fence[j] == open_c:
                depth += 1
            elif fence[j] == close_c:
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        end = j
    else:
        end = fence.find("\n", i)
        if end == -1:
            end = len(fence)
    return fence[m.start():end].rstrip().rstrip(",")


def gm_source_codenames(text):
    """All backtick-wrapped ALL-CAPS source codenames in text, e.g. `ATS`,
    `BLS-OES`. Used to filter Part 1 / Part 1.5 registry rows down to only
    the codenames an agent's own Part 3 block (plus Part 4 fallback row)
    actually cites."""
    return set(re.findall(r"`([A-Z][A-Z0-9\-]{0,14})`", text))


def classify_pack_path_cell(cell):
    """CONTEXT_PACK.md §5 cell -> (pack_top_level_keys, research_top_level_keys).
    Handles the '+ research: a, b, c' suffix and drops any bare token that
    is not a valid top-level key in either schema (see VALID_PACK_TOP_KEYS /
    VALID_RESEARCH_TOP_KEYS): that is the one known source ambiguity in this
    file (the 01 sensei optional cell writes bare 'skill_transfer_notes'
    instead of 'keywords.skill_transfer_notes'); dropping it loses nothing
    because 'keywords' is already pulled in by the cell's other token."""
    if not cell or cell.strip() in ("", "-"):
        return set(), set()
    req_part, research_part = cell, ""
    if "+ research:" in cell:
        req_part, research_part = cell.split("+ research:", 1)
    pack_keys = set()
    for tok in req_part.split(","):
        tok = tok.strip()
        if not tok:
            continue
        top = tok.split(".")[0]
        if top in VALID_PACK_TOP_KEYS:
            pack_keys.add(top)
    research_keys = set()
    for tok in research_part.split(","):
        tok = tok.strip()
        if tok and tok in VALID_RESEARCH_TOP_KEYS:
            research_keys.add(tok)
    return pack_keys, research_keys


def subpath_map(cells, extra_paths=None):
    """One or more CONTEXT_PACK.md §5 cells (+ optional extra dotted paths
    from EXTRA_PACK_PATHS) -> {top_level_key: None | {sub_key, ...}}.
    None means "this agent needs the whole top-level block" (the §5 cell
    named the bare key, e.g. 'personas', with no dot); a set means "only
    these nested fields" (the cell named 'comp.canonical_range', so nothing
    else under 'comp' is this agent's business). A key that shows up both
    ways (one path bare, another dotted) resolves to None: bare wins,
    because it is a strictly larger request. This drives the sub-key
    extraction in context_pack_slice() so a brief carries field SHAPES for
    the paths an agent actually reads or writes, not whole pack sections."""
    result = {}
    for cell in list(cells) + list(extra_paths or []):
        if not cell or cell.strip() in ("", "-"):
            continue
        req_part = cell.split("+ research:", 1)[0]
        for tok in req_part.split(","):
            tok = tok.strip()
            if not tok:
                continue
            segs = tok.split(".", 1)
            top = segs[0]
            if top not in VALID_PACK_TOP_KEYS:
                continue
            if len(segs) == 1:
                result[top] = None  # whole block requested
            elif result.get(top, ()) is not None:
                result.setdefault(top, set()).add(segs[1])
    return result


def extract_pack_block(fence, top, subs):
    """Render one top-level pack.json key's block, narrowed to `subs` (a set
    of second-level keys) when given, or the whole block when subs is None.
    Falls back to the whole block if a requested sub-key isn't found (source
    wording drift is more likely than a genuinely absent field; see the
    module docstring on fail-loud vs fail-quiet)."""
    whole = extract_key_block(fence, top)
    if whole is None or subs is None:
        return whole
    pieces = []
    for sub in sorted(subs):
        piece = extract_key_block(whole, sub, indent=4)
        if piece:
            # A scalar field's captured line may already end
            # '"x", // (req)' (comma before the trailing source comment);
            # move the join comma ahead of that comment instead of adding a
            # second, cosmetically doubled one.
            piece = re.sub(r",(\s*//[^\n]*)$", r"\1", piece)
            pieces.append(piece)
    if not pieces:
        return whole
    return f'  "{top}": {{\n' + ",\n".join(pieces) + f'\n  }},'


def bullets_from_rows(rows, cols, sep=" - "):
    out = []
    for r in rows:
        out.append(sep.join(str(r.get(c, "")).strip() for c in cols if r.get(c)))
    return out


# ---------------------------------------------------------------- loaders


class Sources:
    """Parses the three source files once; every build_*_brief() function
    reads from this shared, already-parsed structure."""

    def __init__(self):
        self.shared_core_text = read(SHARED_CORE_PATH)
        self.shared_core, self.shared_core_order = split_sections(
            self.shared_core_text, level=2)

        self.gm_text = read(GROUNDING_PATH)
        self.gm_parts, self.gm_order = split_sections(self.gm_text, level=2)
        self.gm_part1_rows = parse_md_table(self._gm("PART 1"))
        self.gm_part2_block = self._gm("PART 2")
        self.gm_part3_blocks, _ = split_sections(self._gm("PART 3"), level=3)
        self.gm_part35_rows = parse_md_table(self._gm("PART 3.5"))
        self.gm_part35_notes = self._notes_after_table(self._gm("PART 3.5"))
        self.gm_part4_sub, _ = split_sections(self._gm("PART 4"), level=3)
        self.gm_part4_fallback_rows = parse_md_table(
            self.gm_part4_sub["Per-agent public-source fallback"])
        self.gm_part4_register_rows = parse_md_table(
            self.gm_part4_sub["Source register: what the extractor ingests"])
        self.gm_part15_sub, _ = split_sections(self._gm("PART 1.5"), level=3)
        self.gm_part15_rows = {}
        for tier in ("T1 · Government and official series",
                     "T2 · Industry primary research",
                     "T3 · Aggregators (triangulation only, never a sole source)"):
            self.gm_part15_rows[tier] = parse_md_table(self.gm_part15_sub[tier])
        self.gm_part15_rules = self.gm_part15_sub["Rules for the public layer"]
        self.gm_part5_block = self._gm("PART 5")

        self.cp_text = read(CONTEXT_PACK_PATH)
        self.cp, self.cp_order = split_sections(self.cp_text, level=2)
        self.cp_pack_fence = extract_fenced_json(self.cp["3"])
        self.cp_research_fence = extract_fenced_json(self.cp["3.5"])
        self.cp_market_vocab = self._market_vocab_note()
        self.cp_sec5_rows = parse_md_table(self.cp["5"])

    def _gm(self, prefix):
        for k in self.gm_order:
            if k.startswith(prefix):
                return self.gm_parts[k]
        raise KeyError(f"02_GROUNDING_MATRIX.md heading starting {prefix!r} not found")

    @staticmethod
    def _notes_after_table(section_text):
        """Prose paragraphs that follow the last '|' table row in a section
        (Part 3.5's 'assumptions is a sanctioned extra key' + relay note)."""
        lines = section_text.splitlines()
        last_table_idx = max(
            (i for i, l in enumerate(lines) if l.strip().startswith("|")),
            default=-1)
        return "\n".join(lines[last_table_idx + 1:]).strip()

    def _market_vocab_note(self):
        """The ABUNDANT/BALANCED/TIGHT/SCARCE definition + legacy-term
        mapping table that sits in CONTEXT_PACK.md §3, after the fenced
        pack.json schema block, before §3.5 starts."""
        sec3 = self.cp["3"]
        fence_end = sec3.rfind("```")
        tail = sec3[fence_end + 3:]
        m = re.search(r"(?m)^`market\.classification`.*", tail)
        return tail[m.start():].strip() if m else ""


# ---------------------------------------------------------------- shared-core


def schema_repeat_features(stem):
    """Which of the four repeat-shape features (bars, row_variants, grid,
    points) this agent's OWN bound schema actually uses. Drives
    trim_repeats_paragraph() below: no point explaining the `grid` cell
    vocabulary to an agent whose schema has no grid repeat."""
    if stem is None:
        return {"bars", "row_variants", "grid", "points"}  # qa-gate: audits all 8
    path = os.path.join(SCHEMA_DIR, f"{stem}.content-schema.json")
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)
    feats = set()
    for info in schema.get("repeats", {}).values():
        if info.get("bars_per_row"):
            feats.add("bars")
        if "row_variants" in info:
            feats.add("row_variants")
        if info.get("kind") == "grid":
            feats.add("grid")
        if info.get("kind") == "points":
            feats.add("points")
    return feats


def trim_repeats_paragraph(body, features):
    """00_SHARED_CORE.md §5.2's 'Repeats: ...' paragraph explains four
    repeat shapes (bars, row_variants, grid, points) in one run-on
    paragraph. Keep the sentence for a shape only if `features` says this
    agent's own schema actually has one, plus the two sentences that apply
    unconditionally (empty-repeat honesty, data-count guidance)."""
    m = re.search(
        r"(?ms)^Repeats: a list of row objects.*?data genuinely demands otherwise\.\n",
        body)
    if not m:
        raise ValueError("trim_repeats_paragraph: paragraph not found "
                          "(source section wording changed)")
    sentences = {
        "bars": (r'Bars ride the row\n?as `"bar": 0\.34`.*?both 0 to 1\. ', "bars"),
        "row_variants": (r"A repeat with `row_variants`.*?its variant\nlists\. ", "row_variants"),
        "grid": (r'A `grid` repeat takes.*?`primary \| secondary \| touch \| none \| gap`\. ', "grid"),
        "points": (r'A `points` repeat\ntakes.*?client-company star\. ', "points"),
    }
    para = m.group(0)
    for key, (pat, feat) in sentences.items():
        if feat not in features:
            para, n = re.subn(pat, "", para, count=1, flags=re.S)
            if n == 0:
                raise ValueError(f"trim_repeats_paragraph: sentence for "
                                  f"{key!r} not found (source wording changed)")
    return body[:m.start()] + para + body[m.end():]


def trim_content_contract(body, agent):
    """Trim 00_SHARED_CORE.md §5 to what a brief reader still needs once the
    SCHEMA SUMMARY section (built from the agent's own content-schema.json,
    see schema_summary()) sits alongside it in the same file:
      - §5.1's all-9-agents schema table -> a pointer scoped to this agent.
      - The paragraph after that table ("Beside each schema sits ... Read
        both.") -> dropped: it is instructions to read two files this brief
        exists to replace.
      - §5.2's generic worked JSON example (the {"artifact": "03", ...}
        fence) -> dropped: illustrative only, and schema_summary() gives
        this agent's OWN slot names instead of a generic stand-in. The
        prose rules immediately after the fence (value forms, repeats,
        optionals, toggles) are the actual normative content and stay.
      - §5.2's Repeats paragraph -> trimmed to the repeat shapes (bars,
        row_variants, grid, points) this agent's own schema actually uses;
        see trim_repeats_paragraph().
    """
    table_re = re.compile(
        r"(?m)^\| Agent \| Content schema.*$\n(?:^\|.*$\n?)+")
    if agent in AGENT_SCHEMA:
        stem = AGENT_SCHEMA[agent]
        replacement = (
            f"Your bound content schema: `{stem}.content-schema.json`. "
            f"This brief's SCHEMA SUMMARY section below is the compact form "
            f"(slot names, types, word ranges, repeat/toggle/optional "
            f"structure); it replaces reading the schema JSON and the "
            f"worked example-content JSON directly.\n"
        )
    elif agent == "qa-gate":
        stem = None
        replacement = (
            "A09 QA GATE (you): no bound schema of your own. You audit every "
            "other agent's content JSON against ITS schema; the AUDIT "
            "CONTRACT rules below (§5.2-5.4) are the shape common to all "
            "eight, not any one schema.\n"
        )
    else:
        stem = None
        replacement = ""
    body = table_re.sub(replacement, body, count=1)

    beside_re = re.compile(
        r"(?ms)^Beside each schema sits.*?You never open the template HTML itself\.\n\n")
    body = beside_re.sub("", body, count=1)

    example_re = re.compile(r"(?ms)^```json\n\{\n  \"artifact\": \"03\".*?\n```\n\n")
    body = example_re.sub("", body, count=1)

    if agent in AGENT_SCHEMA or agent == "qa-gate":
        body = trim_repeats_paragraph(body, schema_repeat_features(stem))

    return body


def drop_numbered_item(body, label):
    """Remove one bold-lead numbered item ('-1. **PACK FIRST ...** ...', or
    plain '2. Render each ...' in a Rules: list) up to, but not including,
    the next numbered item at the same list or the section's trailing '---',
    from a 00_SHARED_CORE.md section body. label is the exact leading token
    ('-1', '0.5', '2', ...). Used only to drop items that are independently,
    verifiably restated in every agents/*.md body this fix leaves untouched
    (see the drop-site comments below for the specific grep evidence)."""
    pat = re.compile(
        rf"(?m)^{re.escape(label)}\.\s+(?:\*\*)?.*?(?=^-?\d+(?:\.\d+)?\.\s|^---\s*$)",
        re.S)
    new_body, n = pat.subn("", body, count=1)
    if n == 0:
        raise ValueError(f"drop_numbered_item: label {label!r} not found "
                          f"(source section wording changed; fix the mapping "
                          f"or this function)")
    return new_body


# 00_SHARED_CORE.md §7 SELF-QA is, item by item, a checklist over rules this
# brief already states in full elsewhere in the SAME document (§§1.5-6): see
# the item-by-item mapping in the module docstring's design notes. For the 8
# content-producing agents this brief compacts it to the two items that are
# NOT restated anywhere else in the brief (item 2: no surviving shipped
# example content; item 9: repeat count discipline). qa-gate is the one
# agent that AUDITS other agents against this exact checklist, so it keeps
# the full, uncompacted version.
_SELF_QA_COMPACT = (
    "## 7. SELF-QA BEFORE EMITTING\n\n"
    "Before writing: run the checklist implied by §§1.5-6 above (every slot "
    "filled or sanctioned-null, one pill+method per number, pack values "
    "carried unchanged, zero em dashes/forbidden phrases, one decision per "
    "callout, constraints verbatim or absent, nothing fabricated, handoff "
    "valid). Two items nothing else in this brief states:\n\n"
    "1. No slot still carries the shipped example's content (the Propulsion "
    "Engineer search at Onepromptman). Every value is for THIS search.\n"
    "2. Repeat row counts inside their `data-count` bands, or a stated "
    "reason; empty repeats are empty lists, never one hedged row.\n\n"
    "Content JSON written to `<run folder>/content/<NN>.content.json`; final "
    "message is the §6 summary. No HTML anywhere.\n"
)


def drop_constraints_subsection(body):
    """Strip the whole '**Constraints (eligibility gates)**' subsection
    (intro prose, YAML shape, all 5 rules) out of §4 VOICE AND CONSTRAINTS,
    keeping only Voice. Only scout uses this: scout structurally never
    writes `constraints` (ADAPTATIONS.md item 13g: profile-verbatim only,
    never seeded, never scout's job), so the entire subsection is dead
    weight in scout's brief, unlike every other agent that renders
    constraints somewhere in its artifact."""
    pat = re.compile(r"(?ms)^\*\*Constraints \(eligibility gates\)\*\*.*?(?=^---\s*$)")
    new_body, n = pat.subn("", body, count=1)
    if n == 0:
        raise ValueError("drop_constraints_subsection: marker not found "
                          "(source section wording changed)")
    return new_body


def shared_core_slice(src, agent):
    codes = SHARED_CORE_SECTIONS.get(agent, [])
    if not codes:
        return ""
    parts = []
    for code in codes:
        body = src.shared_core[code]
        if code == "2":
            if agent not in BROAD_SOURCE_AGENTS:
                # Item -1 (PACK FIRST) is restated verbatim in every artifact
                # agent's own RUNTIME preamble ("The pack is the sole source
                # of every cross-artifact decision (shared core §2 step -1):
                # carry its values and pills through unchanged...", present
                # in every agents/*.md file this fix does not touch below the
                # RUNTIME read-line). scout and qa-gate keep it: scout is the
                # one BUILDING the pack this rule protects, qa-gate is the
                # one auditing compliance with it.
                body = drop_numbered_item(body, "-1")
            if agent != "scout":
                # Item 0.5 (USER RESOURCES / config.resources) governs a
                # per-agent KB-root and web-steer override surface that, per
                # ADAPTATIONS.md item 1, resolves from the profile the
                # orchestrator writes, not a runtime choice this brief can
                # change; it is also the single largest item in §2 while
                # being the narrowest edge case. scout is the one agent whose
                # own procedure branches on connector/resource availability
                # per search, so it alone keeps this item.
                body = drop_numbered_item(body, "0.5")
        if code == "4":
            if agent == "scout":
                # scout never writes `constraints` at all (see docstring on
                # drop_constraints_subsection); only Voice survives.
                body = drop_constraints_subsection(body)
            else:
                # Rule 2 (verbatim rendering) is restated near-verbatim in
                # most artifact agents' own METHOD sections (jdbot,
                # calibrate, interview-lab, recruiter-screen) and in
                # qa-gate's own Check 1 ("Paraphrase, softening, expansion,
                # or added legal language is a FAIL"). Rules 1 (empty=no
                # gate) and 5 (never estimate a protected-class population,
                # an absolute line stated nowhere else) stay for everyone.
                # Rule 4 (pass-through-rate estimation) is ALSO restated
                # near-verbatim in atlas.md's own METHOD section ("A
                # constraint filters the funnel only if you can source or
                # estimate its pass-through rate ... (shared core §4)"), so
                # it is dropped for atlas same as everyone else.
                body = drop_numbered_item(body, "2")
                body = drop_numbered_item(body, "4")
        if code == "1.5":
            # The trailing "A pack value that was seeded or imported..."
            # paragraph's two duties are both already stated elsewhere in
            # this same brief: "never upgrade the pill" is §3's own rule
            # ("carry the pack's pill and method through unchanged"), and
            # "carry the caveat into handoff.assumptions" is §6's own rule.
            # Its closing sentence ("a pack path your artifact requires that
            # the pack omits is still missing, halt on it") is restated in
            # every agents/*.md RUNTIME preamble ("a missing named input or
            # required pack path is a NEED_INPUT halt"). Dropped everywhere.
            body = re.sub(
                r"(?ms)^A pack value that was seeded or imported.*?Halt on it\.\n\n",
                "", body, count=1)
        if code == "5":
            body = trim_content_contract(body, agent)
        if code == "7" and agent != "qa-gate":
            body = _SELF_QA_COMPACT
        parts.append(body.strip())
    return "\n\n".join(parts)


# ---------------------------------------------------------------- grounding matrix


def format_registry_rows(rows, id_col, cols):
    out = []
    for r in rows:
        rest = " · ".join(str(r.get(c, "")).strip() for c in cols if r.get(c))
        out.append(f"- {r.get(id_col, '').strip()}: {rest}")
    return "\n".join(out)


# scout and qa-gate are the two broad, cross-source agents (scout researches
# across the whole registry to build the pack; qa-gate audits provenance
# against Part 2's precedence table and candidate-data routing against
# Part 5). They get the fuller registry/precedence/access slice. The 8
# artifact-producing agents' own Part 3 block already names its bound
# sources, retrieval patterns, and codenames in prose, and every one of
# their agents/*.md bodies already restates the Part 5 "never put internal
# strings, comp figures, or names into a web query" routing rule verbatim
# (grep confirms this per-agent, see the F2 run report's fidelity check) and
# the Part 3.5 handoff keys verbatim in their own HANDOFF KEYS section, so
# repeating Part 1 / Part 1.5 / Part 2 / Part 3.5 / Part 5 for them is
# redundant with content they already have. This is the single largest cut
# in this file's size budget.
BROAD_SOURCE_AGENTS = {"scout", "qa-gate"}


def grounding_matrix_slice(src, agent):
    if agent == "relay":
        return ""

    if agent == "scout":
        block_headings = SCOUT_SOURCE_AGENTS
    else:
        block_headings = [AGENT_CODE[agent]]

    own_blocks = []
    for h in block_headings:
        match = next((k for k in src.gm_part3_blocks if k.startswith(h)), None)
        if match is None:
            raise KeyError(f"02_GROUNDING_MATRIX.md Part 3 block for {h!r} not found")
        own_blocks.append(src.gm_part3_blocks[match].strip())
    own_block_text = "\n\n".join(own_blocks)

    # Part 4 per-agent fallback row(s): the standalone/no-connector reading
    # list. Kept for every agent EXCEPT the three whose own agents/*.md
    # RESEARCH PLAYBOOK already names this exact codename set in prose
    # (grep-confirmed): atlas.md's "Web:" line spells out BLS-OES ·
    # BLS-JOLTS · ACS · CENSUS-MIG · HIRINGLAB · LIGHTCAST · WARN · LAYOFFS ·
    # EDGAR · NEWSROOM verbatim; jdbot.md's "Public fallback:" line spells
    # out BLS-OES · ONET · public postings verbatim; calibrate.md's timing
    # bullet spells out BLS-OES, OFLC, LEVELS, BLS-JOLTS, WARN, LAYOFFS
    # verbatim. Every other producer agent's playbook only gestures at
    # "public benchmark sources" / "O*NET-equivalent" without naming
    # codenames, so this row is the sole place those agents get them.
    PART4_REDUNDANT_FOR = {"atlas", "jdbot", "calibrate"}
    if agent in PART4_REDUNDANT_FOR:
        fallback_rows = []
    else:
        fallback_rows = [r for r in src.gm_part4_fallback_rows
                          if any(r.get("Agent", "").startswith(h) for h in block_headings)]
    fallback_text = "\n".join(
        f"- {r.get('Agent')}: {r.get('Public sources')}" for r in fallback_rows)

    out = ["## GROUNDING MATRIX SLICE (from `02_GROUNDING_MATRIX.md`)", ""]
    if agent == "scout":
        out.append("Your sources are the union of the A07 + A01 + A03 blocks "
                    "(per scout.md's own GROUNDING section):")
    out.append(own_block_text)
    if fallback_text:
        out += ["", "**Part 4 · standalone / no-connector reading list:**", fallback_text]

    if agent not in BROAD_SOURCE_AGENTS:
        return "\n".join(out)

    codenames = set()
    for blk in own_blocks:
        codenames |= gm_source_codenames(blk)
    for r in fallback_rows:
        codenames |= gm_source_codenames(r.get("Public sources", ""))

    # Part 1's T0-system registry (ATS/WIKI/CSR binding details) matters
    # operationally to the agents that QUERY those systems and to qa-gate,
    # which cross-checks provenance tiers against it. scout is the other
    # broad-source agent but its own SOURCE ORDER section (scout.md,
    # untouched) already covers "connected internal systems via MCP tools"
    # generically; Part 1.5 (the public layer, scout's default path) below
    # carries the sources scout actually cites most.
    if agent == "scout":
        part1_text = ""
    else:
        part1_rows = [r for r in src.gm_part1_rows if r.get("ID", "").strip("`") in codenames]
        part1_text = format_registry_rows(
            part1_rows, "ID", ["Source role", "Tier", "Binding"])

    part15_lines = []
    # scout works through WebSearch/WebFetch, not raw API endpoints, and its
    # own RESEARCH PLAYBOOK (scout.md, untouched) already states what each
    # codename grounds, inline, per pack section ("market: BLS-OES
    # baseline... BLS-JOLTS for tightness, HIRINGLAB/LIGHTCAST for posting
    # demand", etc: every codename in this table is named there). So both
    # "Grounds" (what it's for) and "Access" (the URL) are redundant with
    # content scout.md already carries; source name plus tier code is what
    # this table adds. qa-gate, the other broad-source agent, keeps the
    # full row: it has no equivalent per-codename restatement of its own,
    # and cross-checks whether a producer cited the right KIND of source.
    part15_cols = ("Source", "Note") if agent == "scout" \
        else ("Source", "Grounds", "Access", "Note")
    for tier, rows in src.gm_part15_rows.items():
        code_col = "Code"
        matched = [r for r in rows if r.get(code_col, "").strip("`") in codenames]
        if matched:
            part15_lines.append(f"**{tier}**")
            cols = [c for c in part15_cols if c in matched[0]]
            part15_lines.append(format_registry_rows(matched, code_col, cols))
    part15_text = "\n".join(part15_lines)

    # Part 3.5 handoff-schema row(s): qa-gate audits every producer's
    # conformance so it gets the full table; scout emits no handoff block.
    if agent == "qa-gate":
        part35_rows = src.gm_part35_rows
    else:
        part35_rows = []
    part35_text = ""
    if part35_rows:
        # qa-gate's check 6 is "does the content JSON's handoff.keys match
        # Part 3.5 for that artifact": Producer + the exact keys is the
        # whole check. Consumers (data-flow documentation) and Budget
        # (a producer-side token cap, not something qa-gate measures) are
        # dropped from this table for qa-gate only.
        cols = ["Producer", "Exact keys in `handoff`"]
        rows_fmt = "\n".join(
            "| " + " | ".join(r.get(c, "") for c in cols) + " |" for r in part35_rows)
        header = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
        part35_text = header + "\n" + rows_fmt + "\n\n" + src.gm_part35_notes

    if part1_text:
        out += ["", "**Part 1 · source registry, filtered to codenames above:**", part1_text]
    if part15_text:
        out += ["", "**Part 1.5 · public data sources, filtered to codenames above:**", part15_text]
    part2_text = src.gm_part2_block.split("\n", 1)[1].strip()
    if agent == "scout":
        # scout never builds an interview plan or rubric (INTERVIEW LAB's
        # job); this is the one Part 2 row with no scout section behind it.
        part2_text = re.sub(
            r"(?m)^\| Interview process, rubrics, interviewer names \|.*\n", "",
            part2_text, count=1)
    out += ["", "**Part 2 · source-of-truth precedence:**", part2_text]
    if part35_text:
        out += ["", "**Part 3.5 · consolidated handoff schema, every producer "
                "(you audit conformance across all of them):**", part35_text]
    # The "Routing rule" bullet ("no internal string, band figure, employee
    # name, or candidate name may appear inside a web search query") is
    # restated verbatim in both scout.md and qa-gate.md bodies already
    # (grep-confirmed, see F2 run report); the rest of Part 5 (ATS/WIKI
    # scope, the comp file location, the constraints/protected-class rule)
    # is not restated anywhere and stays.
    part5_text = re.sub(
        r"(?ms)^- \*\*Routing rule\*\*:.*?\n(?=- )", "",
        src.gm_part5_block.split("\n", 1)[1].strip() + "\n")
    out += ["", "**Part 5 · access, scopes, and sensitive-data routing:**",
            part5_text.strip()]
    return "\n".join(out)


# ---------------------------------------------------------------- context pack


def context_pack_slice(src, agent):
    if agent == "relay":
        return ""

    out = ["## CONTEXT PACK SLICE (from `CONTEXT_PACK.md`)", ""]

    # §2 pv shape: universal to every pack reader/writer.
    out += ["**§2 · the pilled value (pv) shape, every quantitative claim in "
            "the pack:**", "", "```json",
            '{"value": "$150-175K", "pill": "Sourced", '
            '"method": "OFLC 2026 filings, 14 rows", "as_of": "2026-06"}',
            "```",
            "`pill` is exactly Sourced, Estimate, or Internal. `method` is "
            "required, never empty. Nothing downstream may upgrade a pill "
            "it reads from the pack.", ""]

    if agent in AGENT_PACK_ROW:
        row = next(r for r in src.cp_sec5_rows if r["Artifact"] == AGENT_PACK_ROW[agent])
        out += [f"**§5 · your row in the per-artifact pack requirements table:**", "",
                f"- Required: {row['Required pack paths']}",
                f"- Optional but used: {row['Optional but used']}",
                "",
                "A missing REQUIRED path is Class A: halt with NEED_INPUT, "
                "`kind: pack_key`. The pack is the sole source of market "
                "classification and carries exactly ONE canonical comp range "
                "(`comp.canonical_range`), which every artifact states "
                "identically; disagree from your own lookup and you keep the "
                "pack value, add your finding, raise a Caution, never fork "
                "the number.", ""]
        pmap = subpath_map(
            [row["Required pack paths"], row["Optional but used"]],
            extra_paths=EXTRA_PACK_PATHS.get(agent))
        # Every §5 row names bare "role" (always in scope), which
        # subpath_map() resolves to None (whole block). But only
        # calibrate's own body names `hm_names` / `recruiter_names`
        # ("Names are per-requisition: hm_names and recruiter_names are
        # provided per run by the orchestrator and may print verbatim in
        # this artifact"), and no agent body reads `org_descriptor` or
        # `slug` directly (they compose role.org from location/work_model/
        # team). Narrow to the fields every artifact actually renders;
        # calibrate alone keeps the whole block.
        if agent != "calibrate":
            pmap["role"] = {"title", "level", "company", "location",
                             "work_model", "team"}
        pmap.setdefault("role", None)
        req_keys, req_research = classify_pack_path_cell(row["Required pack paths"])
        opt_keys, opt_research = classify_pack_path_cell(row["Optional but used"])
        research_keys = req_research | opt_research
        if agent in EXTRA_PACK_PATHS:
            out += [f"*(Fidelity override: `{', '.join(EXTRA_PACK_PATHS[agent])}` added "
                     f"beyond the §5 row above because {agent}.md's own METHOD "
                     f"section reads it; see F2 run report for the source-file "
                     f"gap this covers.)*", ""]
    elif agent == "scout":
        pmap = {k: None for k in VALID_PACK_TOP_KEYS}  # writes every field
        research_keys = set(VALID_RESEARCH_TOP_KEYS) - {"pack_version", "role_slug", "built"}
    elif agent == "qa-gate":
        # Check 3 (pack fidelity) names these paths explicitly ("comp.
        # canonical_range", "market.classification", "spec.requirements",
        # personas, keywords, messaging urgency/comp_angle); check 1 needs
        # constraints; check 3c needs caveats; check 4 also names
        # `spec.must_have_skills` explicitly ("A06's competency columns
        # cover every spec.must_have_skills entry... A08's spot-checks trace
        # to spec.must_have_skills and keywords.title_synonyms"), a second
        # spec field beyond `requirements`, grep-confirmed against
        # agents/qa-gate.md. Check 3c also names the top-level `built_from`
        # array directly ("A market.classification, funnel, comp guidance,
        # or personas section whose built_from is only user_stated is a
        # HIGH finding"). `channels`/`targets`/`timing` are not named by any
        # check and are dropped (unlike scout, qa-gate never has to WRITE
        # the pack, only trace values already IN content JSON back to it).
        pmap = {
            "role": {"title", "level", "company"},  # check 4: consistency of title/level
            "spec": {"requirements", "must_have_skills"},
            "market": {"classification"},
            "comp": {"canonical_range"}, "keywords": None, "personas": None,
            "messaging": {"urgency", "comp_angle"},
            "constraints": None, "caveats": None, "built_from": None,
        }
        # Check 3's traceability list plus check 3c's seeded-values check;
        # `demand_blocs` and `persona_detail` aren't named by any check.
        research_keys = {"dossiers", "metros", "proof_points", "quadrant"}
    else:
        pmap, research_keys = {}, set()

    if agent == "qa-gate":
        out += ["**§5 · required pack paths per artifact "
                "(you audit fidelity across every artifact, not just one; "
                "optional-but-used column omitted, see the row's own agent "
                "brief for that):**", ""]
        out += [f"- {r['Artifact']}: {r['Required pack paths']}" for r in src.cp_sec5_rows]
        out += [""]

    if pmap:
        out += ["**§3 · pack.json schema, keys and fields you read or write "
                "(NOT the full file: only the paths named above, field shapes "
                "only, `...` marks a worked-example placeholder value):**", "",
                "```json"]
        for key in sorted(pmap, key=lambda k: (k != "role", k)):
            blk = extract_pack_block(src.cp_pack_fence, key, pmap[key])
            if blk:
                out.append(blk if blk.endswith(",") else blk + ",")
        out += ["```", ""]

    if "market" in pmap and src.cp_market_vocab:
        # Full vocab (with the legacy LOOSE/MODERATE/CRITICAL mapping table,
        # a note for anyone auditing or updating OLD agent prose) only for
        # scout: it is the sole writer of market.classification and the one
        # agent that must never regress to the legacy terms. Atlas carries
        # the classification through from the pack and already names all
        # four current terms itself (METHOD: "Classify the effective
        # supply-to-demand ratio ABUNDANT, BALANCED, TIGHT, or SCARCE"), so
        # it never needs the legacy-mapping table; everyone else that merely
        # reads `market.classification` as an optional path also gets the
        # one normative sentence: the enum and the "only vocabulary" rule.
        if agent == "scout":
            out += [src.cp_market_vocab, ""]
        else:
            short = src.cp_market_vocab.split("\n\n")[0].split(". ", 2)
            out += [". ".join(short[:2]) + ".", ""]

    if research_keys:
        out += ["**§3.5 · pack-research.json schema, keys you read "
                "(only atlas/hunter/shakespeare/scout/qa-gate read this file "
                "at all):**", "", "```json"]
        for key in sorted(research_keys):
            blk = extract_key_block(src.cp_research_fence, key)
            if blk:
                out.append(blk + ",")
        out += ["```", ""]

    if agent in ("scout", "relay"):
        out += ["**§4 · freshness table (per pack section, not per pack):**", "",
                src.cp["4"].split("\n", 1)[1].strip(), ""]

    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- schema summary


# Compact form: "name (type N-M)[*]" -- backticks and the word "words"
# dropped (the header line states the units once for the whole section);
# "*" flags a synthetic slot instead of a bracketed phrase repeated per slot.
def format_slot(name, info, indent="- "):
    words = info.get("words", {})
    w = f"{words.get('min', '?')}-{words.get('max', '?')}"
    synth = "*" if info.get("synthetic") else ""
    return f"{indent}{name} ({info.get('type')} {w}){synth}"


def format_repeat(name, info):
    kind = info.get("kind", "rows")
    count = info.get("count")
    lines = []
    if kind == "rows":
        bars = info.get("bars_per_row", 0)
        bar_forms = info.get("bar_forms")
        bar_note = ""
        if bars:
            bar_note = f" bars={bars}"
            if bar_forms:
                bar_note += f"({'/'.join(bar_forms)})"
        lines.append(f"- {name} [rows n={count}{bar_note}]")
        for sn, si in info.get("row_slots", {}).items():
            lines.append("  " + format_slot(sn, si))
        nested = info.get("nested")
        if nested:
            for nk, ninfo in nested.items():
                lines.append(f"  - nested {nk} [n={ninfo.get('count')}]")
                for sn, si in ninfo.get("row_slots", {}).items():
                    lines.append("    " + format_slot(sn, si))
    elif kind == "grid":
        lines.append(
            f"- {name} [grid n={count} cols={info.get('cols')} "
            f"data_cols={info.get('data_cols')} label={info.get('label_slot')} "
            f"cells={info.get('cell_vocab')}]")
    elif kind == "points":
        lines.append(
            f"- {name} [points n={count} label={info.get('label_slot')} "
            f"fields=label/x/y, optional size/accent]")
    else:
        lines.append(f"- {name} [{kind} n={count}]")
    return "\n".join(lines)


def schema_summary(stem):
    path = os.path.join(SCHEMA_DIR, f"{stem}.content-schema.json")
    with open(path, encoding="utf-8") as f:
        schema = json.load(f)

    out = [f"## SCHEMA SUMMARY · `{stem}.content-schema.json` "
           f"(template: `{schema['template']}`)", "",
           "Format: `name (type MIN-MAX)`, word count not the full JSON or "
           "worked example prose; a slot ranged 24-24 wants 24 words, not 8 "
           "and not 60. `*` = synthetic: prose the template generator found "
           "beyond the named data-slot elements, filled exactly like any "
           "other slot, never left as the shipped example text.", ""]

    out.append("### Top-level slots")
    for name, info in schema.get("slots", {}).items():
        out.append(format_slot(name, info))
    out.append("")

    out.append("### Repeats")
    for name, info in schema.get("repeats", {}).items():
        out.append(format_repeat(name, info))
    out.append("")

    if schema.get("standalone_bars"):
        out.append(f"### Standalone bars\n{schema['standalone_bars']}\n")
    if schema.get("toggles"):
        out.append(
            f"### Toggles\n{schema['toggles']} "
            f"(booleans selecting which sections render; choose defaults in "
            f"the template's `state = {{...}}` logic block, never delete an "
            f"`<sc-if>` wrapper to hide a section)\n")
    if schema.get("optionals"):
        out.append("### Optional blocks")
        for opt in schema["optionals"]:
            ctx = opt.get("context", "")
            out.append(f"- `{opt.get('id')}` (handoff_block={opt.get('handoff_block')}): {ctx}")
        out.append("")
    if schema.get("handoff_slots"):
        out.append(f"### Handoff slots\n{schema['handoff_slots']}\n")

    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- assembly


THIS_SCRIPT_PATH = os.path.abspath(__file__)

# Root every hashed path is made relative to, so the fingerprint depends only
# on tree-relative paths and file bytes, never on where the tree is checked
# out. This is the skill root (parent of scripts/ and references/).
SKILL_ROOT = os.path.normpath(os.path.join(HERE, ".."))


def _relkey(path):
    """Path key fed into the fingerprint hash: POSIX-style, relative to
    SKILL_ROOT, so identical trees checked out at different absolute
    locations (or on different OSes) hash identically."""
    return os.path.relpath(os.path.abspath(path), SKILL_ROOT).replace(os.sep, "/")


def source_fingerprint(input_paths):
    """First 12 hex chars of sha256 over this script's own bytes plus every
    listed input file's bytes, concatenated in the given (fixed) order, each
    file separated by its SKILL_ROOT-relative path so two different files
    that happen to share content never collide. Pure function of file
    content on disk plus tree-relative paths: no absolute paths, no clock,
    no env, no randomness. Same sources in -> same fingerprint out, on any
    machine, at any checkout location, forever; edit any listed source (or
    this script) and the fingerprint changes."""
    h = hashlib.sha256()
    for path in [THIS_SCRIPT_PATH] + list(input_paths):
        h.update(_relkey(path).encode("utf-8"))
        h.update(b"\0")
        with open(path, "rb") as f:
            h.update(f.read())
        h.update(b"\0")
    return h.hexdigest()[:12]


def header(agent, extra_inputs=None):
    inputs = ["00_SHARED_CORE.md", "02_GROUNDING_MATRIX.md", "CONTEXT_PACK.md"]
    input_paths = list(SOURCE_FILES)
    if agent in AGENT_SCHEMA:
        schema_name = f"content-schemas/{AGENT_SCHEMA[agent]}.content-schema.json"
        inputs.append(schema_name)
        input_paths.append(os.path.join(REF, schema_name))
    if extra_inputs:
        inputs += extra_inputs
    fingerprint = source_fingerprint(input_paths)
    return (
        "<!--\n"
        f"GENERATED FILE. Do not hand-edit.\n"
        f"Generator: {GENERATOR_NAME}\n"
        f"Source fingerprint: {fingerprint}\n"
        f"Inputs: {', '.join(inputs)}\n"
        f"Regenerate: python3 skills/talent-one/scripts/build_briefs.py\n"
        "-->\n"
    )


def build_agent_brief(src, agent):
    """The 8 artifact-producing agents share one assembly shape: shared-core
    slice, grounding-matrix slice, context-pack slice, schema summary."""
    label = AGENT_CODE.get(agent, "SCOUT (union of A07 + A01 + A03 sources)")
    parts = [header(agent),
              f"# BRIEF · {label}", "",
              "Precompiled slice of this kit's four reference files, scoped "
              "to what this agent needs. Read this file only; it replaces "
              "reading 00_SHARED_CORE.md, CONTEXT_PACK.md, "
              "02_GROUNDING_MATRIX.md, and this agent's content-schema + "
              "example-content pair in full.", "",
              "## SHARED CORE SLICE (from `00_SHARED_CORE.md`)", "",
              shared_core_slice(src, agent), "",
              grounding_matrix_slice(src, agent), "",
              context_pack_slice(src, agent), ""]
    if agent in AGENT_SCHEMA:
        parts.append(schema_summary(AGENT_SCHEMA[agent]))
    return "\n".join(parts).rstrip() + "\n"


def build_scout_brief(src):
    return build_agent_brief(src, "scout")


def build_qa_gate_brief(src):
    return build_agent_brief(src, "qa-gate")


def build_relay_brief(src):
    parts = [
        header("relay"),
        "# BRIEF · RELAY (planning broker)", "",
        "relay has no shared-core slice (it never writes provenance, "
        "content, or a handoff, and never halts via NEED_INPUT) and no "
        "grounding-matrix slice (it does no research). Its whole job runs "
        "off CONTEXT_PACK.md's structural tables, reproduced here in full "
        "since relay computes a UNION across whichever artifacts were "
        "requested and so needs every row, not one.", "",
        "## CONTEXT PACK: FULL §5 REQUIREMENTS TABLE", "",
    ]
    cols = ["Artifact", "Required pack paths", "Optional but used"]
    header_row = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
    rows_fmt = "\n".join(
        "| " + " | ".join(r.get(c, "") for c in cols) + " |" for r in src.cp_sec5_rows)
    parts += [header_row, rows_fmt, "",
              "Union the requested artifacts' rows: that union is scout's "
              "scope when a build or sectional refresh is needed. Note "
              "which artifacts also need `pack-research.json` (03, 04, 05).",
              "", "## CONTEXT PACK: §4 FRESHNESS TABLE", "",
              src.cp["4"].split("\n", 1)[1].strip(), "",
              "## CONTEXT PACK: §1 FILES AND LOCATIONS", "",
              src.cp["1"].split("\n", 1)[1].strip(), "",
              "## CONTEXT PACK: §6 SEEDING RULES (for the seed-candidate step)", "",
              src.cp["6"].split("\n", 1)[1].strip(), "",
              "## CONTEXT PACK: market.classification vocabulary", "",
              src.cp_market_vocab, "",
              "## PHASE STRUCTURE (fixed, from relay.md itself, reproduced "
              "for quick reference)", "",
              "Phase 1: Context Pack build/refresh/import (scout, or "
              "skill-seeded). Phase 2: every requested artifact agent, all "
              "parallel, each fed the pack files. Phase 3: deterministic "
              "render (`scripts/render.py`), then qa-gate when 2+ artifacts "
              "were built. No inter-artifact DAG: the pack carries every "
              "cross-artifact decision.", ""]
    return "\n".join(parts).rstrip() + "\n"


BUILDERS = {a: (lambda src, a=a: build_agent_brief(src, a)) for a in AGENT_CODE}
BUILDERS["scout"] = build_scout_brief
BUILDERS["qa-gate"] = build_qa_gate_brief
BUILDERS["relay"] = build_relay_brief


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                     help="exit 1 if regenerating would change any file on disk")
    ap.add_argument("--agent", action="append",
                     help="only build this agent's brief (repeatable); default: all")
    args = ap.parse_args(argv)

    for p in SOURCE_FILES:
        if not os.path.isfile(p):
            print(f"FATAL: source file missing: {p}", file=sys.stderr)
            return 2

    src = Sources()
    os.makedirs(BRIEFS_DIR, exist_ok=True)

    agents = args.agent or ALL_AGENTS
    changed = []
    results = []
    for agent in agents:
        if agent not in BUILDERS:
            print(f"FATAL: unknown agent {agent!r}", file=sys.stderr)
            return 2
        content = BUILDERS[agent](src)
        out_path = os.path.join(BRIEFS_DIR, f"{agent}.md")
        existing = read(out_path) if os.path.isfile(out_path) else None
        # Byte-identical rebuilds are the idempotency contract. The header's
        # "Source fingerprint:" line is a hash of file content (this script
        # plus the brief's source files), not a timestamp, so it is stable
        # across runs on different days and only churns when a real source
        # edit would make the brief stale anyway.
        is_changed = existing != content
        if is_changed and not args.check:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
        if is_changed:
            changed.append(agent)
        results.append((agent, out_path, len(content.encode("utf-8"))))

    print(f"{'agent':<18} {'bytes':>7} {'KB':>7}  path")
    for agent, out_path, size in results:
        print(f"{agent:<18} {size:>7} {size/1024:>6.1f}K  {out_path}")

    # Enforcement-by-audit: the soft 20KB target warns; the 24KB hard ceiling
    # FAILS the build, in --check mode too. (Nothing executes between an
    # agent's tool calls, so per-spawn reading cost is only enforceable here,
    # at build time, where the briefs are made.)
    warn = [(a, s) for a, _, s in results if 20 * 1024 < s <= HARD_CEILING_BYTES]
    over = [(a, s) for a, _, s in results if s > HARD_CEILING_BYTES]
    if warn:
        print("\nover 20KB soft target:", ", ".join(f"{a} ({s/1024:.1f}K)" for a, s in warn),
              file=sys.stderr)
    if over:
        print(f"\nOVER {HARD_CEILING_BYTES // 1024}KB HARD CEILING (build fails):",
              ", ".join(f"{a} ({s/1024:.1f}K)" for a, s in over), file=sys.stderr)

    if args.check:
        if changed:
            print(f"\n--check: STALE ({', '.join(changed)}); run without --check to regenerate.",
                  file=sys.stderr)
            return 1
        if over:
            print("\n--check: briefs up to date but over the hard ceiling.", file=sys.stderr)
            return 1
        print("\n--check: all briefs up to date.")
        return 0

    print(f"\nWrote {len(results)} briefs to {BRIEFS_DIR} "
          f"({len(changed)} changed).")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
