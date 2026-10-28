#!/usr/bin/env python3
"""Infer slot types from the templates' shipped worked examples, and check that
`skills/talent-one/references/SLOT_SCHEMA.json` still covers the templates.

Every template ships filled with the worked example. That filled content is the
only machine-readable statement of what a slot is *for*, so it is what types are
inferred from: `hub.ownership` holding "62%" says the slot is a percent.

    python3 tools/extract_slot_schema.py            # print the inferred schema
    python3 tools/extract_slot_schema.py --check    # does SLOT_SCHEMA.json match the
                                                    # templates' slots and repeats?

The committed SLOT_SCHEMA.json is hand-corrected (its `types` are authoritative);
this script never overwrites it. Print, diff, and carry over only what you mean to.
`--check` compares structure only (which slot and repeat names exist, and in which
templates); a different inferred type is a hand correction, not drift. Anything
ambiguous is emitted with `review: true` for a human to resolve.
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent
REF = MODULE / "skills" / "talent-one" / "references"
TEMPLATES = REF / "templates"
SCHEMA = REF / "SLOT_SCHEMA.json"


class SlotReader(HTMLParser):
    """Collect the text content of every [data-slot] and [data-repeat]."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # open (tag, slot_name or None)
        self.text = defaultdict(list)
        self.repeats = {}        # name -> data-count
        self.bars = set()        # slots carrying data-bar

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        slot = a.get("data-slot")
        if "data-repeat" in a:
            self.repeats[a["data-repeat"]] = a.get("data-count", "")
        if slot and "data-bar" in a:
            self.bars.add(slot)
        if tag not in ("br", "img", "hr", "meta", "link", "input"):
            self.stack.append((tag, slot))
        elif slot:
            self.text[slot].append("")

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        for _, slot in self.stack:
            if slot:
                self.text[slot].append(data)


# Ordered: first match wins, so put the specific patterns above the general.
NUM = r"[\d,]+(?:\.\d+)?"
DASH = r"[-–]"  # hyphen or en dash; em dashes are banned pack-wide

PATTERNS = [
    ("pill",           r"^(Sourced|Estimate|Modeled|Internal|Derived)\b"),
    # Ranges before their singular counterparts, or "$120-145K" would match
    # the plain currency pattern on its first half and stop.
    ("currency_range",
     rf"^\$?{NUM}\s*[KkMm]?\s*{DASH}\s*\$?{NUM}\s*[KkMm]?$"),
    ("count_range",     rf"^{NUM}\s*{DASH}\s*{NUM}$"),
    ("currency",        rf"^[~<>]?\${NUM}\s*[KkMm]?$"),
    ("percent",         r"^[~<>+-]?[\d.]+\s*%$"),
    ("ratio",           r"^[\d.]+\s*:\s*[\d.]+$"),
    ("duration",        r"^(D\d+|[\d.]+\s*(min|minutes|hr|hours|days?|weeks?|months?|yrs?|years?)|"
                        r"days?|weeks?|months?|hours?|minutes?)$"),
    ("date",            r"^([A-Z]{3}\s+\d{4}|\d{4}|\d{4}-\d{2}-\d{2})$"),
    ("count",           rf"^[~<>+-]?{NUM}\s*[KkMmBb]?\+?$"),
    ("empty_cell",      r"^[-–—]$"),
]

# Short controlled vocabularies that render as chips. Case-insensitive.
CHIP_WORDS = {
    "high", "med-high", "med", "med-low", "low", "abundant", "balanced",
    "tight", "scarce", "critical", "loose", "moderate", "must-have",
    "calibrated", "flex", "nice-to-have", "non-negotiable", "advance",
    "hold", "decline", "yes", "no", "none", "house", "oracle", "primary",
    "secondary", "touch", "gap", "s", "a", "b", "c",
}


def infer_type(value: str, slot: str, is_bar: bool):
    # is_bar is metadata only (a same-tag data-bar co-occurrence, which only
    # the Pattern Library's documentation markup actually does; real artifact
    # templates put the bar on a sibling div). The slot's own text still
    # drives its type, so a bar-adjacent count like "~1.7M" reads as `count`,
    # not as the normalized 0-1 fraction check_fill.py validates separately.
    v = value.strip()
    if not v:
        return "prose", True
    for name, pat in PATTERNS:
        if re.match(pat, v, re.I):
            # The optional "$" in the range patterns lets a plain count like
            # "1,800-2,400" match currency_range on a technicality. Demote it
            # to count_range unless a dollar sign is actually present.
            if name == "currency_range" and "$" not in v:
                name = "count_range"
            return name, False
    if v.lower().strip(" ·") in CHIP_WORDS:
        return "chip", False
    words = len(v.split())
    if slot.endswith((".title", ".name", ".label", ".term", ".stage", ".segment")):
        return "label", False
    if words <= 3:
        return "label", True          # short but unrecognized: worth a look
    if words <= 25:
        return "prose_short", False
    return "prose_long", False


def infer(templates: Path = TEMPLATES) -> tuple[dict, dict]:
    """(slots, repeats) inferred from every TK_*.dc.html under `templates`."""
    slots, repeats, seen = {}, {}, defaultdict(list)
    files = sorted(glob.glob(str(templates / "TK_*.dc.html")))
    if not files:
        raise SystemExit(f"no templates under {templates}")
    for path in files:
        tk = "_".join(os.path.basename(path).split("_")[:2])
        p = SlotReader()
        p.feed(open(path, encoding="utf-8").read())
        for slot, chunks in p.text.items():
            val = re.sub(r"\s+", " ", html.unescape("".join(chunks))).strip()
            seen[slot].append((tk, val, slot in p.bars))
        for name, count in p.repeats.items():
            entry = repeats.setdefault(name, {"count": count, "templates": []})
            if tk not in entry["templates"]:
                entry["templates"].append(tk)
    for slot, occurrences in sorted(seen.items()):
        vals = [v for _, v, _ in occurrences if v]
        is_bar = any(b for _, _, b in occurrences)
        sample = max(vals, key=len) if vals else ""
        typ, review = infer_type(sample, slot, is_bar)
        lens = [len(v.split()) for v in vals] or [0]
        entry = {
            "type": typ,
            "templates": sorted({t for t, _, _ in occurrences}),
            "words": {"min": min(lens), "max": max(lens)},
            "example": sample[:160],
        }
        if review:
            entry["review"] = True
        if is_bar:
            entry["bar_paired"] = True
        slots[slot] = entry
    return slots, repeats


def check(schema_path: Path = SCHEMA, templates: Path = TEMPLATES) -> list[str]:
    """Structural drift between SLOT_SCHEMA.json and the templates, as messages."""
    committed = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    slots, repeats = infer(templates)
    have_s, have_r = committed.get("slots", {}), committed.get("repeats", {})
    vocab = set(committed.get("types", {}))
    out = []
    for name in sorted(set(slots) - set(have_s)):
        out.append(f"slot {name!r} is in {slots[name]['templates']} but not in the schema")
    for name in sorted(set(have_s) - set(slots)):
        out.append(f"schema slot {name!r} is in no template")
    for name in sorted(set(slots) & set(have_s)):
        a, b = sorted(slots[name]["templates"]), sorted(have_s[name].get("templates", []))
        if a != b:
            out.append(f"slot {name!r}: templates {a}, schema says {b}")
        if vocab and have_s[name].get("type") not in vocab:
            out.append(f"slot {name!r}: type {have_s[name].get('type')!r} is not in `types`")
    for name in sorted(set(repeats) - set(have_r)):
        out.append(f"repeat {name!r} is in {repeats[name]['templates']} but not in the schema")
    for name in sorted(set(have_r) - set(repeats)):
        out.append(f"schema repeat {name!r} is in no template")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--templates", default=str(TEMPLATES))
    ap.add_argument("--schema", default=str(SCHEMA))
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when SLOT_SCHEMA.json and the templates disagree on structure")
    args = ap.parse_args(argv)
    if args.check:
        drift = check(Path(args.schema), Path(args.templates))
        for line in drift:
            print(f"DRIFT  {line}")
        print(f"slot schema: {len(drift)} structural difference(s)")
        return 1 if drift else 0
    slots, repeats = infer(Path(args.templates))
    print(json.dumps({"version": "inferred", "slots": slots, "repeats": repeats},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
