"""Content contracts for Talent One artifacts: the deterministic layer of the eval.

The content schemas under references/content-schemas/ are regenerated from the templates
(`render.py schema`), so constraints written into them die on the next template edit. The
contract lives beside each schema instead, as TK_NN.contract.json, DERIVED from the shipped
worked example (never invented):

  required     every slot the example fills with non-empty text
  numeric      slots whose example value states a claim figure (money, percent, or a count of
               1,000+; artifact numbers and years are furniture); produced content must state
               a figure there too
  repeats      every repeat block the example fills: at least one item; item_keys are the
               keys every example item fills (optional_keys vary across items)
  toggles      the example's toggle set (keys only; values may differ)

Three commands:

  derive          (re)write TK_NN.contract.json for every example; idempotent
  check-examples  every example satisfies its own contract (the contracts are not vacuous)
  check           validate produced content: --content <json> [--pack <pack.json>]
                  [--workspace <dir>] (finds */TK_NN*.content.json under the dir)

`check` fails on: a required slot missing or empty, a numeric slot with no digit, a repeat
below its minimum or with missing item keys, unexpanded `{{`, an em dash (U+2014), or
placeholder text (lorem, TBD, TODO, [insert, placeholder, XXX). With --pack it also fails
when a money or percent figure, or an integer of 1,000 or more, in the content does not
appear anywhere in the pack: every number an artifact states must trace to the Context
Pack, and the pack is the only source of market and comp figures (00_SHARED_CORE.md).
Four-digit years and the artifact's own numbering (TK_02, Artifact 02) are furniture, not
claims, and are exempt.

Exit 0 clean, 1 with findings (one line each), 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE.parent / "references" / "content-schemas"

PLACEHOLDER_RE = re.compile(
    r"lorem ipsum|\bTBD\b|\bTODO\b|\[insert|\[placeholder\]|<placeholder>|placeholder text|\bXXX\b",
    re.IGNORECASE,
)
MONEY_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?\s?[KkMm]?")
PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s?%")
BIGINT_RE = re.compile(
    r"(?<![\d.$])\d{1,3}(?:,\d{3})+(?![\d%])|(?<![\d.$,])\d{4,}(?![\d%,])"
)
# A bare K/M currency token with no leading `$` -- how comp.low/comp.high ship
# per the content schema ("type": "currency", format "<amount>K", no `$`).
BARE_KM_RE = re.compile(r"\b\d{2,3}(?:\.\d+)?[KkMm]\b")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
FURNITURE_RE = re.compile(r"(?:Talent Kit|Artifact|TK)[ _·\-]*0?\d{1,2}\b")


# ----------------------------------------------------------------------------- contracts


def _text_values(obj) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out += _text_values(v)
    elif isinstance(obj, list):
        for v in obj:
            out += _text_values(v)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(str(obj))
    return out


def _has_number(s: str) -> bool:
    return bool(re.search(r"\d", s))


def load_overrides(schemas: Path, n: str) -> dict:
    """Hand-authored exceptions beside the schema: TK_NN.contract-overrides.json with
    `optional: {slot: reason}`. A slot the worked example fills but a real run may honestly
    leave empty (an eligibility gate when the profile has no constraints, an EEO statement
    when the brand doc supplies none) is listed here WITH its reason from the agent brief.
    Nothing else is overridable: the example remains the source of every other bound."""
    p = schemas / f"TK_{n}.contract-overrides.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    bad = [k for k in d if k != "optional"]
    if bad:
        raise SystemExit(f"{p.name}: only `optional` may be overridden, not {bad}")
    opt = d.get("optional") or {}
    if not isinstance(opt, dict) or any(not str(v).strip() for v in opt.values()):
        raise SystemExit(
            f"{p.name}: `optional` maps slot -> reason; every slot needs a reason"
        )
    return d


def _schema_row_count(schema: dict | None, name: str) -> tuple[int, int] | None:
    """(lower, upper) from a content-schema.json repeat's `count` field
    (`"3-8"` -> `(3, 8)`), or None when the repeat isn't in the schema or its
    `count` isn't a "lo-hi" range."""
    spec = ((schema or {}).get("repeats") or {}).get(name) or {}
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", str(spec.get("count", "")))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _schema_row_min(schema: dict | None, name: str) -> int | None:
    """The template's designed lower row count (`count: "3-8"` -> 3), when the schema states one."""
    bounds = _schema_row_count(schema, name)
    return bounds[0] if bounds else None


def _schema_row_max(schema: dict | None, name: str) -> int | None:
    """The template's designed upper row count (`count: "2-4"` -> 4), when the schema states one."""
    bounds = _schema_row_count(schema, name)
    return bounds[1] if bounds else None


def derive_contract(
    example: dict, overrides: dict | None = None, schema: dict | None = None
) -> dict:
    slots = example.get("slots") or {}
    optional = (overrides or {}).get("optional") or {}
    required = sorted(
        k
        for k, v in slots.items()
        if isinstance(v, str) and v.strip() and k not in optional
    )
    # numeric = slots whose example value states a CLAIM figure (money, percent, pool count),
    # not furniture digits (artifact numbers, years, footer marks)
    numeric = sorted(k for k in required if claims(FURNITURE_RE.sub("", slots[k])))
    repeats = {}
    for name, items in (example.get("repeats") or {}).items():
        if not isinstance(items, list) or not items:
            continue
        dicts = [it for it in items if isinstance(it, dict)]
        if not dicts:
            continue
        always = set(dicts[0])
        union: set[str] = set()
        for it in dicts:
            always &= {k for k, v in it.items() if str(v).strip()}
            union |= set(it)
        repeats[name] = {
            # floor/ceiling = the template's designed range when the schema states one,
            # else 1 (floor) or the example's own row count (ceiling)
            # floor stays 1: the template's lower count is layout guidance, and a floor above
            # the number of events the pack records forces an invented row (three live runs
            # each manufactured a third ledger calibration when the pack recorded two)
            "min": 1,
            "max": _schema_row_max(schema, name) or len(items),
            "item_keys": sorted(always),  # every example item fills these
            "optional_keys": sorted(
                union - always
            ),  # shape varies across example items
        }
    return {
        "template": example.get("template"),
        "derived_from": "example-content",
        "required": required,
        "optional": dict(sorted(optional.items())),
        "numeric": numeric,
        "repeats": repeats,
        "toggles": sorted((example.get("toggles") or {}).keys()),
    }


def artifact_numbers(example_or_schema_path: Path) -> str:
    m = re.search(r"TK_(\d{2})", example_or_schema_path.name)
    return m.group(1) if m else ""


def derive_all(schemas: Path = SCHEMAS) -> list[Path]:
    written = []
    for ex in sorted(schemas.glob("TK_*.example-content.json")):
        n = artifact_numbers(ex)
        schema_path = schemas / f"TK_{n}.content-schema.json"
        schema = (
            json.loads(schema_path.read_text(encoding="utf-8"))
            if schema_path.exists()
            else None
        )
        contract = derive_contract(
            json.loads(ex.read_text(encoding="utf-8")),
            load_overrides(schemas, n),
            schema,
        )
        out = schemas / f"TK_{n}.contract.json"
        text = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            # open() rather than Path.write_text: write_text takes newline= only from 3.10
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        written.append(out)
    return written


# ----------------------------------------------------------------------------- checks


def claims(text: str) -> set[str]:
    """Money (with or without a leading `$`), percent, and large-integer tokens in
    text, normalized for comparison. pack_numbers() calls this per pack text value
    too, so a bare K/M token (comp.low/comp.high's own shape) is recognized on
    both sides of the trace, not just the content side."""
    found: set[str] = set()
    for m in MONEY_RE.finditer(text):
        found.add(_norm_num(m.group(0)))
    for m in BARE_KM_RE.finditer(text):
        found.add(_norm_num(m.group(0)))
    for m in PERCENT_RE.finditer(text):
        found.add(_norm_num(m.group(0)))
    for m in BIGINT_RE.finditer(text):
        tok = m.group(0)
        if YEAR_RE.match(tok.replace(",", "")):
            continue
        found.add(_norm_num(tok))
    return found


def _norm_num(tok: str) -> str:
    t = tok.replace("$", "").replace(",", "").replace(" ", "").replace("%", "").strip()
    mult = 1
    if t and t[-1] in "KkMm":
        mult = 1000 if t[-1] in "Kk" else 1_000_000
        t = t[:-1]
    try:
        val = float(t) * mult
    except ValueError:
        return tok
    return str(int(val)) if val == int(val) else str(val)


def _first_number(value: str) -> float | None:
    """The first digit run in `value`, commas stripped, as a float -- or None
    when there is none. Tolerant parsing for a cover.metrics cell that may
    read "318", "Grade 9", or "9.1 (Flesch-Kincaid)"."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", value)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def pack_numbers(pack: dict) -> set[str]:
    nums: set[str] = set()
    for s in _text_values(pack):
        nums |= claims(s)
        # bare integers and decimals in pack values count too (pct 0.20, ratio 1:9)
        for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", s):
            tok = m.group(0)
            nums.add(_norm_num(tok))
            # a bare fraction (pack states 0.53) also allows content to state its
            # percent rendering (content states "53%"): both are the same figure
            try:
                x = float(tok.replace(",", ""))
            except ValueError:
                x = None
            if x is not None and 0 < x < 1:
                nums.add(_norm_num(f"{round(x * 100)}"))
    # money ranges like "$210-245K" also imply the upper bound with the suffix applied
    for s in _text_values(pack):
        for m in re.finditer(r"\$\s?(\d[\d,]*)\s?-\s?(\d[\d,]*)\s?([KkMm])", s):
            nums.add(_norm_num("$" + m.group(1) + m.group(3)))
            nums.add(_norm_num("$" + m.group(2) + m.group(3)))
    return nums


QUOTE_CHARS = "\"'“”‘’"
# Characters gate.1 may still hold once every disqualifying constraint's own
# text is removed from it: whitespace, quote marks, and light separators
# (comma, semicolon, middle dot, pipe, ampersand, dash) joining multiple
# constraints together -- never a stray word of jdbot's own prose.
GATE_RESIDUE_CHARS = set(" \t\r\n" + QUOTE_CHARS + ",;·|&/+-–—.")


def _pack_constraints(pack: dict | None) -> list[dict]:
    if not isinstance(pack, dict):
        return []
    cs = pack.get("constraints")
    return [c for c in cs if isinstance(c, dict)] if isinstance(cs, list) else []


WORD5_RE = re.compile(r"[A-Za-z]{5,}")


def _words5(s: str) -> set[str]:
    """Every letters-only run of 5+ characters in `s`, lowercased -- the
    shared vocabulary used to trace a ledger row back to a pack requirement
    without demanding an exact-string match."""
    return {w.lower() for w in WORD5_RE.findall(s)}


def _pack_requirement_words(pack: dict) -> set[str]:
    """5+-letter words across the pack's intake wording: every `spec.requirements[].name`,
    the other `spec` values (education, years, skills, trade-off lock), and each
    constraint's label and requirement. A ledger row's `before` column restates one of
    these; a row that shares no word with any of them is invented intake history."""
    words: set[str] = set()
    spec = (pack or {}).get("spec") or {}
    for key, val in spec.items():
        if key == "requirements" and isinstance(val, list):
            for r in val:
                if isinstance(r, dict) and isinstance(r.get("name"), str):
                    words |= _words5(r["name"])
        elif isinstance(val, dict) and isinstance(val.get("value"), str):
            words |= _words5(val["value"])
        elif isinstance(val, str):
            words |= _words5(val)
        elif isinstance(val, list):
            words |= _words5(" ".join(str(x) for x in val if isinstance(x, str)))
    for c in (pack or {}).get("constraints") or []:
        if isinstance(c, dict):
            words |= _words5(
                " ".join(str(c.get(k, "")) for k in ("label", "requirement"))
            )
    return words


def _html_slot_values(content: dict) -> list[tuple[str, str]]:
    """(path, raw html) for every slot or repeat-row value shaped
    `{"html": ...}` -- the RAW markup, before _slot_text's tag-stripping,
    since a style attribute lives in the tag itself."""
    out: list[tuple[str, str]] = []
    for k, v in (content.get("slots") or {}).items():
        if isinstance(v, dict) and isinstance(v.get("html"), str):
            out.append((f"slots.{k}", v["html"]))
    for name, rows in (content.get("repeats") or {}).items():
        if not isinstance(rows, list):
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if isinstance(v, dict) and isinstance(v.get("html"), str):
                    out.append((f"repeats.{name}[{i}].{k}", v["html"]))
    return out


ENVELOPE = ("slots", "repeats")


def check_content(
    content: dict,
    contract: dict,
    pack: dict | None = None,
    warnings: list[str] | None = None,
) -> list[str]:
    """Findings fail the check and the exit code. `warnings` (an out-parameter --
    pass a list to collect them, or omit to discard) never do: a warning names
    something to look at, not something proven wrong (e.g. a ledger row that may
    legitimately quote a supplied posting the pack never sees)."""
    findings: list[str] = []
    if warnings is None:
        warnings = []
    if not isinstance(content.get("slots"), dict) or not isinstance(
        content.get("repeats"), dict
    ):
        top = [k for k in content if k not in ENVELOPE][:6]
        findings.append(
            "content JSON is flat: no `slots`/`repeats` envelope (top-level keys start "
            f"{top}); the renderer reads slots under `slots` and rows under `repeats`"
        )
    # the renderer reads `standalone_bars` as a positional LIST and the other two as objects
    for key, want in (
        ("standalone_bars", list),
        ("optionals", dict),
        ("toggles", dict),
    ):
        val = content.get(key)
        if isinstance(val, (list, dict)) and len(val) == 0:
            continue  # empty is empty in either shape; the renderer treats it so
        if val is not None and not isinstance(val, want):
            findings.append(
                f"envelope key `{key}` must be {'a list' if want is list else 'an object'}, "
                f"got {type(val).__name__}"
            )
    slots = content.get("slots") or {}
    for k in contract["required"]:
        v = slots.get(k)
        if not isinstance(v, str) or not v.strip():
            findings.append(f"required slot missing or empty: {k}")
    for k in contract["numeric"]:
        v = slots.get(k)
        if isinstance(v, str) and v.strip() and not _has_number(v):
            findings.append(f"numeric slot carries no number: {k} = {v[:60]!r}")
    reps = content.get("repeats") or {}
    for name, spec in contract["repeats"].items():
        items = reps.get(name)
        if not isinstance(items, list) or len(items) < spec["min"]:
            findings.append(f"repeat {name}: fewer than {spec['min']} item(s)")
            continue
        max_n = spec.get("max")
        if max_n is not None and len(items) > max_n:
            findings.append(f"repeat {name} has {len(items)} rows, ceiling {max_n}")
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                findings.append(f"repeat {name}[{i}]: not an object")
                continue
            missing = [
                key for key in spec["item_keys"] if not str(it.get(key, "")).strip()
            ]
            if missing:
                findings.append(f"repeat {name}[{i}]: missing {missing}")
    for path, text in _walk_text(content):
        if "{{" in text:
            findings.append(f"unexpanded placeholder in {path}")
        if "—" in text:
            findings.append(f"em dash in {path}")
        m = PLACEHOLDER_RE.search(text)
        if m:
            findings.append(f"placeholder text in {path}: {m.group(0)!r}")
    if pack is not None:
        allowed = pack_numbers(pack)
        for path, text in _walk_text(content):
            scrubbed = FURNITURE_RE.sub("", text)
            for tok in sorted(claims(scrubbed)):
                if tok not in allowed:
                    findings.append(f"number not in pack: {tok} (in {path})")

        # F1: a constraint the pack carries is a constraint the content must
        # render -- verbatim, and (when disqualifying) inside gate.1, which may
        # hold MULTIPLE disqualifying constraints but nothing beyond them.
        constraints = _pack_constraints(pack)
        if constraints:
            all_text = [t for _, t in _walk_text(content)]
            for c in constraints:
                req = str(c.get("requirement", "")).strip()
                if not req:
                    continue
                if not any(req in t for t in all_text):
                    findings.append(f"constraint missing: {req[:80]}")

            disqualifying_reqs = [
                str(c.get("requirement", "")).strip()
                for c in constraints
                if c.get("disqualifying") and str(c.get("requirement", "")).strip()
            ]
            if disqualifying_reqs:
                gate_val = slots.get("gate.1")
                gate_text = gate_val if isinstance(gate_val, str) else ""
                missing_in_gate = [r for r in disqualifying_reqs if r not in gate_text]
                residue = gate_text
                for r in disqualifying_reqs:
                    residue = residue.replace(r, "")
                residue_ok = len(residue) <= 12 and all(
                    ch in GATE_RESIDUE_CHARS for ch in residue
                )
                if missing_in_gate or not residue_ok:
                    findings.append(
                        "gate.1 must contain every disqualifying constraint "
                        "verbatim, nothing else"
                    )

        # F2 / F3: handoff shape -- an object with a `keys` object and a
        # `blocked` string; a real blocker in `blocked` is a finding, not
        # something a run should ship as if it were clean.
        handoff = content.get("handoff")
        if not isinstance(handoff, dict):
            findings.append("handoff must be an object")
        else:
            if not isinstance(handoff.get("keys"), dict):
                findings.append("handoff.keys must be an object")
            blocked = handoff.get("blocked")
            if not isinstance(blocked, str) or not blocked.strip():
                findings.append("handoff.blocked must be a string")
            elif not blocked.strip().lower().startswith("nothing"):
                findings.append(
                    "handoff.blocked declares a blocker (the run is not clean; "
                    "resolve the cause or return NEED_INPUT, never rewrite blocked "
                    f"to Nothing): {blocked.strip()[:80]}"
                )

        # F4: a WARNING (never a finding -- see check_content's docstring) when a
        # ledger row's `before` shares no 5+-letter word with the pack's own
        # intake wording. `before` may legitimately quote a supplied posting the
        # pack never sees, so this flags for a human/agent to look, it does not
        # fail the check on its own.
        ledger_rows = reps.get("ledger.rows")
        if isinstance(ledger_rows, list):
            pack_words = _pack_requirement_words(pack)
            if pack_words:
                for row in ledger_rows:
                    if not isinstance(row, dict):
                        continue
                    before = row.get("ledger.before")
                    if not isinstance(before, str) or not before.strip():
                        continue
                    if not (_words5(before) & pack_words):
                        warnings.append(
                            "warning: ledger.before not traceable to the pack's "
                            f"intake wording: {before[:80]}"
                        )

        # F5: jd.meta carries the posted range verbatim (comp.canonical_range).
        canonical_range = (
            ((pack.get("comp") or {}).get("canonical_range") or {}).get("value")
            if isinstance(pack, dict)
            else None
        )
        jd_meta = slots.get("jd.meta")
        if (
            isinstance(canonical_range, str)
            and canonical_range.strip()
            and isinstance(jd_meta, str)
            and canonical_range not in jd_meta
        ):
            findings.append(
                f"jd.meta does not carry comp.canonical_range verbatim: {canonical_range[:80]}"
            )

        # F7: no style attribute inside an html slot (the design system owns
        # styling; an inline style is untracked drift the renderer cannot audit).
        for path, html in _html_slot_values(content):
            if "style=" in html:
                findings.append(f"html slot carries a style attribute: {path}")

        # F8: cover.metrics must restate the validator's own posting word count
        # and reading grade, not a number jdbot computed itself. Tolerant of
        # format: the FIRST number in the value, commas stripped; the grade
        # compares at one decimal ("Grade 9" passes 9.0, "Grade 19.0" does not).
        metrics_rows = reps.get("cover.metrics")
        if isinstance(metrics_rows, list):
            rd = readability_report(content)
            if rd is not None and rd.get("scope") == "posting":
                for row in metrics_rows:
                    if not isinstance(row, dict):
                        continue
                    label = str(row.get("metric.label", ""))
                    value = str(row.get("metric.value", ""))
                    if re.search(r"word count", label, re.IGNORECASE):
                        got = _first_number(value)
                        if got is None or int(got) != rd["words"]:
                            findings.append(
                                f"cover.metrics word count {value} != validator {rd['words']}"
                            )
                    elif re.search(r"reading", label, re.IGNORECASE):
                        got = _first_number(value)
                        if got is None or round(got, 1) != round(rd["grade"], 1):
                            findings.append(
                                f"cover.metrics reading level {value!r} != "
                                f"validator grade {rd['grade']:.1f}"
                            )
    return findings


def _walk_text(obj, path="content"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_text(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_text(v, f"{path}[{i}]")


VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")


def count_syllables(word: str) -> int:
    """Approximate syllable count: vowel groups, minus a silent trailing `e`
    (but not a `le` ending, e.g. "table"). A small heuristic, not a
    dictionary lookup -- good enough for a length guide, not a rubric."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(VOWEL_GROUP_RE.findall(w))
    if w.endswith("e") and not w.endswith("le") and n > 1:
        n -= 1
    return max(n, 1)


JD_PREFIX = "jd."


def _slot_text(v) -> str | None:
    """A slot value's own prose text: a bare string, a `{"pill": ...}`
    provenance object's pill text, or a `{"html": ...}` object's text with
    tags stripped (jd.intro-shaped posting-body slots ship this way). A
    closing block tag or line break becomes a sentence boundary FIRST, so a
    multi-paragraph slot with no terminal punctuation on an inner paragraph
    still counts as separate sentences rather than one run-on; a paragraph
    that already ends with its own period does not then double-count (the
    resulting ".." collapses back to one "." )."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        if isinstance(v.get("pill"), str):
            return v["pill"]
        if isinstance(v.get("html"), str):
            html = re.sub(r"</(?:p|li|h[1-6]|div)\s*>|<br\s*/?>", ". ", v["html"])
            html = re.sub(r"<[^>]+>", " ", html)
            return re.sub(r"\.\s*\.", ".", html)
    return None


def _readability_sources(content: dict) -> list[tuple[str, str]]:
    """(key, text) pairs for every slot and repeat-row value that carries
    prose text: `key` is the slot name, or the owning repeat's name for a
    row value, so callers can scope by key prefix (e.g. "jd." for the
    candidate-facing posting). Unfiltered by length."""
    out: list[tuple[str, str]] = []
    for k, v in (content.get("slots") or {}).items():
        text = _slot_text(v)
        if text is not None and text.strip():
            out.append((k, text))
    for name, rows in (content.get("repeats") or {}).items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for v in row.values():
                text = _slot_text(v)
                if text is not None and text.strip():
                    out.append((name, text))
    return out


def readability_texts(content: dict) -> list[str]:
    """Every prose text (over 8 words) across ALL slots and repeat rows,
    unscoped by key prefix -- the population a person actually reads as
    prose, not chip labels, ids, or short slot values."""
    return [t for _, t in _readability_sources(content) if len(t.split()) > 8]


def flesch_kincaid_grade(text: str) -> float:
    """Flesch-Kincaid Grade Level over a single `text`, using count_syllables
    as the syllable estimator. 0.0 when there is no word to measure."""
    return _flesch_kincaid_grade_multi([text])


def _flesch_kincaid_grade_multi(texts: list[str]) -> float:
    """Flesch-Kincaid Grade Level summed across independent texts: each
    text's own word/sentence/syllable counts are tallied separately first
    and only then combined into one formula application, so a slot with no
    terminal punctuation is never glued onto its neighbor's sentence."""
    total_words = total_sentences = total_syllables = 0
    for text in texts:
        words = re.findall(r"[A-Za-z']+", text)
        if not words:
            continue
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        total_words += len(words)
        total_sentences += max(len(sentences), 1)
        total_syllables += sum(count_syllables(w) for w in words)
    if not total_words:
        return 0.0
    return (
        0.39 * (total_words / total_sentences)
        + 11.8 * (total_syllables / total_words)
        - 15.59
    )


VERBATIM_JD_SLOTS = {"jd.eeo", "jd.benefits"}


def readability_report(content: dict) -> dict | None:
    """Readability over the candidate-facing posting (every slot or repeat
    whose key starts with "jd.") when the content has one -- the posting is
    what a candidate actually reads, not the ledger, rail, or comp rows
    beside it -- else over every qualifying prose text in the content.
    Returns None when there is nothing to measure, else
    {"grade": float, "words": int, "scope": "posting" | "all"}: `words` is
    the total word count across every text in scope (unfiltered by length,
    so short posting lines still count toward the total, VERBATIM_JD_SLOTS
    included); `grade` is the Flesch-Kincaid grade over the over-8-word
    texts in that same scope, EXCLUDING VERBATIM_JD_SLOTS (jd.eeo,
    jd.benefits): brand-doc text jdbot copies verbatim and may not rewrite,
    so its reading level is not jdbot's to fix and must not move the grade
    it is told to act on."""
    sources = _readability_sources(content)
    if not sources:
        return None
    slot_keys = (content.get("slots") or {}).keys()
    repeat_keys = (content.get("repeats") or {}).keys()
    has_jd_scope = any(str(k).startswith(JD_PREFIX) for k in slot_keys) or any(
        str(k).startswith(JD_PREFIX) for k in repeat_keys
    )
    if has_jd_scope:
        scoped = [(k, t) for k, t in sources if k.startswith(JD_PREFIX)]
        scope = "posting"
    else:
        scoped = sources
        scope = "all"
    if not scoped:
        return None
    words = sum(len(t.split()) for _, t in scoped)
    grade_texts = [
        t for k, t in scoped if len(t.split()) > 8 and k not in VERBATIM_JD_SLOTS
    ]
    grade = _flesch_kincaid_grade_multi(grade_texts)
    return {"grade": grade, "words": words, "scope": scope}


def readability_grade(content: dict) -> float | None:
    """Back-compat convenience: just the grade from readability_report(), or
    None when there is nothing to measure."""
    report = readability_report(content)
    return report["grade"] if report else None


def contract_for(content_path: Path, contract_path: Path | None) -> Path:
    if contract_path:
        return contract_path
    n = artifact_numbers(content_path)
    if not n:
        # jdbot writes `<run>/content/02.content.json`; the number is the file's own prefix
        m = re.match(r"(\d{2})\.content\.json$", content_path.name)
        n = m.group(1) if m else ""
    if not n:
        m = re.search(
            r"TK_(\d{2})",
            json.loads(content_path.read_text(encoding="utf-8")).get("template", ""),
        )
        n = m.group(1) if m else ""
    if not n:
        raise SystemExit(
            f"validate_content: cannot infer artifact number for {content_path}"
        )
    return SCHEMAS / f"TK_{n}.contract.json"


def render_strict(content_path: Path, contract_path: Path) -> list[str]:
    """Render the content through render.py --strict into a temp dir; the renderer's own
    missing-slot report is the finding. This is the same path a real run takes."""
    import subprocess
    import tempfile

    n = re.search(r"TK_(\d{2})", contract_path.name).group(1)
    template = next(
        iter((HERE.parent / "references" / "templates").glob(f"TK_{n}_*.dc.html")), None
    )
    ds = next(
        iter((HERE.parent / "references" / "templates" / "_ds").glob("*-ds")), None
    )
    if template is None or ds is None:
        return [f"render: no template or design system for TK_{n}"]
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / f"TK_{n}.html"
        proc = subprocess.run(
            [
                sys.executable,
                str(HERE / "render.py"),
                "render",
                "--template",
                str(template),
                "--schema",
                str(SCHEMAS / f"TK_{n}.content-schema.json"),
                "--content",
                str(Path(content_path).resolve()),
                "--ds",
                str(ds),
                "--out",
                str(out),
                "--strict",
            ],
            cwd=str(HERE.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        text = proc.stdout
        i = text.find("{")
        try:
            rep = json.loads(text[i:]) if i >= 0 else {}
        except json.JSONDecodeError:
            rep = {}
        if proc.returncode == 0 and out.exists():
            return []
        if not rep:
            tail = (
                proc.stderr.strip().splitlines()
                or proc.stdout.strip().splitlines()
                or ["?"]
            )[-1]
            return [f"render crashed (exit {proc.returncode}): {tail[:160]}"]
        missing = rep.get("missing") or []
        errors = rep.get("errors") or []
        msg = f"render --strict failed: {len(missing)} missing slot(s)"
        if missing:
            msg += f" ({', '.join(str(m) for m in missing[:5])}{', ...' if len(missing) > 5 else ''})"
        if errors:
            msg += f"; errors: {'; '.join(str(e)[:80] for e in errors[:2])}"
        return [msg]


# ----------------------------------------------------------------------------- CLI


def cmd_derive(_args) -> int:
    for p in derive_all():
        print(f"derived {p.name}")
    return 0


def cmd_check_examples(_args) -> int:
    bad = 0
    for ex in sorted(SCHEMAS.glob("TK_*.example-content.json")):
        n = artifact_numbers(ex)
        cpath = SCHEMAS / f"TK_{n}.contract.json"
        if not cpath.exists():
            print(f"TK_{n}: no contract (run derive)")
            bad += 1
            continue
        contract = json.loads(cpath.read_text(encoding="utf-8"))
        schema_path = SCHEMAS / f"TK_{n}.content-schema.json"
        fresh = derive_contract(
            json.loads(ex.read_text(encoding="utf-8")),
            load_overrides(SCHEMAS, n),
            json.loads(schema_path.read_text(encoding="utf-8"))
            if schema_path.exists()
            else None,
        )
        if fresh != contract:
            print(f"TK_{n}: contract stale against its example (run derive)")
            bad += 1
        findings = check_content(json.loads(ex.read_text(encoding="utf-8")), contract)
        for f in findings:
            print(f"TK_{n}: {f}")
        bad += len(findings)
        if not findings and fresh == contract:
            print(
                f"TK_{n}: ok ({len(contract['required'])} required, "
                f"{len(contract['numeric'])} numeric, {len(contract['repeats'])} repeats)"
            )
    print("check-examples: clean" if not bad else f"check-examples: {bad} finding(s)")
    return 0 if not bad else 1


def cmd_check(args) -> int:
    targets: list[Path] = []
    if args.content:
        targets.append(Path(args.content))
    if args.workspace:
        ws = Path(args.workspace)
        targets += sorted(
            p for p in ws.rglob("*.content.json") if "example-content" not in p.name
        )
        targets += sorted(
            p for p in ws.rglob("TK_*.json") if p not in targets and "content" in p.name
        )
    targets = list(dict.fromkeys(targets))
    if not targets:
        print("validate_content: no content file found")
        return 1
    pack = None
    if args.pack:
        pack = json.loads(Path(args.pack).read_text(encoding="utf-8"))
    elif args.workspace:
        cand = sorted(Path(args.workspace).rglob("pack.json"))
        if cand:
            pack = json.loads(cand[0].read_text(encoding="utf-8"))
    total = 0
    for t in targets:
        try:
            content = json.loads(t.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"{t.name}: not valid JSON ({e})")
            total += 1
            continue
        cpath = contract_for(t, Path(args.contract) if args.contract else None)
        contract = json.loads(cpath.read_text(encoding="utf-8"))
        warnings: list[str] = []
        findings = check_content(content, contract, pack, warnings)
        if args.render:
            findings += render_strict(t, cpath)
        for f in findings:
            print(f"{t.name}: {f}")
        for w in warnings:
            print(f"{t.name}: {w}")
        total += len(findings)
        if not findings:
            print(
                f"{t.name}: ok"
                + (" (every number traces to the pack)" if pack else "")
                + (" (renders --strict)" if args.render else "")
            )
        rd = readability_report(content)
        if rd is not None:
            if rd["scope"] == "posting":
                print(
                    f"{t.name}: readability: posting {rd['words']} words, "
                    f"grade {rd['grade']:.1f} (guide: 10 or under)"
                )
                print(
                    f"{t.name}: set cover.metrics: {rd['words']} words / "
                    f"grade {rd['grade']:.1f}"
                )
            else:
                print(
                    f"{t.name}: readability: grade {rd['grade']:.1f} "
                    f"(guide: 10 or under)"
                )
    print("check: clean" if not total else f"check: {total} finding(s)")
    return 0 if not total else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="validate_content.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("derive").set_defaults(fn=cmd_derive)
    sub.add_parser("check-examples").set_defaults(fn=cmd_check_examples)
    c = sub.add_parser("check")
    c.add_argument("--content")
    c.add_argument("--contract")
    c.add_argument("--pack")
    c.add_argument("--workspace")
    c.add_argument(
        "--render",
        action="store_true",
        help="also render each content file with render.py --strict; a missing slot fails",
    )
    c.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
