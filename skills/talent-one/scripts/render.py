#!/usr/bin/env python3
"""Talent One deterministic renderer. Version 1.0.

Artifact HTML never passes through a model: agents emit content JSON, this script
fills the bound template. Subcommands:

  schema    --template T --slot-types SLOT_SCHEMA.json --out S.json
            Build the content schema for a template (shipped, build-time).
            Also runs lint_template() and, if it finds anything, prints a
            non-fatal WARNING per finding to stderr and lists them under the
            schema JSON's "furniture_warnings" key.
  extract   --template T --schema S.json --doc FILLED.html --out C.json
            Reverse a filled document (or the template's own worked example)
            into content JSON. Update mode and migration use this.
  render    --template T --schema S.json --content C.json --ds DSDIR --out OUT.html
            [--mode light|dark|dancheong] [--brand --bh-primary=#123456 ...]
            [--handoffs HANDOFFS.json --role SLUG]
            Fill the template deterministically and inline the design system.
  verify    --template T --schema S.json --doc OUT.html [--out REPORT.json]
            Machine QA: geometry agreement, surviving example text, em dashes,
            forbidden phrases, pill vocabulary, repeat counts, template
            furniture (lint_template(), reported as HIGH findings).
  lint-template --template T [--out REPORT.json]
            Template-furniture lint standalone: flags unslotted template text
            on the verbatim-copy surface (short badge/tick text a data-repeat
            base row renders as-is or copies positionally onto later rows;
            short doc-level text below the synthetic-slot floor) that looks
            like real comp/date/domain data -- the surface class that let
            propulsion-demo dollar figures ship into a client document
            undetected. See lint_template().
  validate-pack --pack pack.json [--research pack-research.json] [--out REPORT.json]
            Structural validation of a Context Pack.

Dependency: beautifulsoup4 (html.parser backend only). If missing:
  pip install beautifulsoup4 --break-system-packages
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Comment, Tag
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "render.py needs beautifulsoup4. Run: pip install beautifulsoup4 --break-system-packages\n")
    sys.exit(2)

# ---------------------------------------------------------------- constants

PILL_STYLES = {
    "Sourced": {"color": "var(--bh-success)", "background": "#EEF6F1",
                "border": "1px solid #BFDCCB"},
    "Estimate": {"color": "var(--bh-warning)", "background": "#FAF0E6",
                 "border": "1px solid #E3CDB4"},
    "Internal": {"color": "var(--bh-primary)", "background": "#DCE6F2",
                 "border": "1px solid #C9D6E6"},
}

HEAT_STRENGTH = {
    "primary":   {"bar": "1",    "background": "var(--bh-primary)", "outline": None},
    "secondary": {"bar": "0.65", "background": "#7FA5CC",           "outline": None},
    "touch":     {"bar": "0.3",  "background": "#DCE6F2",           "outline": None},
    "none":      {"bar": None,   "background": "#F0EDE6",           "outline": None},
    "gap":       {"bar": None,   "background": "#F0EDE6",
                  "outline": "2px solid var(--bh-accent)"},
}
HEAT_REVERSE = {"var(--bh-primary)": "primary", "#7FA5CC": "secondary",
                "#DCE6F2": "touch", "#F0EDE6": "none"}

FORBIDDEN_PHRASES = [
    "i hope this finds you well", "came across your profile", "exciting opportunity",
    "quick question", "touch base", "reach out", "pick your brain", "i wanted to",
    "rockstar", "ninja", "guru", "best in class", "fast-paced environment",
    "competitive salary", "world-class", "passionate about",
]

# Consumers line per artifact, for the human handoff block. In 1.0 data flows
# through the Context Pack; this table documents which artifacts use the data.
CONSUMERS = {
    "01": "A02 JD-BOT · A03 ATLAS · A06 INTERVIEW LAB · A08 RECRUITER SCREEN (via Context Pack)",
    "02": "A04 HUNTER · A09 QA GATE (via Context Pack)",
    "03": "A02 JD-BOT · A04 HUNTER · A05 SHAKESPEARE (via Context Pack)",
    "04": "A05 SHAKESPEARE (via Context Pack)",
    "05": "A09 QA GATE",
    "06": "A09 QA GATE",
    "07": "A01 SENSEI · A02 JD-BOT · A03 ATLAS · A04 HUNTER · A05 SHAKESPEARE · A06 INTERVIEW LAB · A08 RECRUITER SCREEN (via Context Pack)",
    "08": "A09 QA GATE",
}

AGENT_BY_ARTIFACT = {"01": "SENSEI", "02": "JD-BOT", "03": "ATLAS", "04": "HUNTER",
                     "05": "SHAKESPEARE", "06": "INTERVIEW LAB", "07": "CALIBRATE",
                     "08": "RECRUITER SCREEN"}

EM_DASH = "—"

# Unslotted direct text at or above this length is worked-example PROSE, not a
# short structural badge/label. build_schema() turns paths this long into
# synthetic slots (F1 fix); render_rows' positional-copy branch only copies
# unslotted text shorter than this straight from the template (badge-length).
MIN_SYNTHETIC_LEN = 45
# Top-level (outside repeats/optionals) uses a stricter floor: the 1.0.1 live
# QA run showed sub-45 worked-example furniture (quadrant axis labels, email
# annotations) surviving into client documents. Row-level keeps 45 so the
# badge positional patch stays intact.
MIN_SYNTHETIC_LEN_DOC = 25

# Worked-example DOMAIN language for the Propulsion Engineer / Onepromptman
# demo search verify()'s "surviving example text" check scans the RENDERED
# DOC for. lint_template() (below) reuses this exact object -- not a copy of
# the pattern -- so the two scans can never drift apart. Any OTHER use of the
# studio name (e.g. a drifted "(c) 2026 Onepromptman" credit) still flags:
# that is wording drift, not sanctioned branding.
DOMAIN_MARKERS = re.compile(
    r"propulsion|thruster|hot[- ]?fire|spacecraft|turbopump|feed[- ]system"
    r"|onepromptman|cryogenic|combustion|test[- ]stand", re.I)
# The sanctioned footer credit is the one legitimate place the studio name
# appears; text carrying the exact sanctioned phrase is exempt from
# DOMAIN_MARKERS, both in verify() and in lint_template().
SANCTIONED_CREDIT = "built with talent one by onepromptman"

# ---------------------------------------------------------------- small helpers


def read(path):
    return Path(path).read_text(encoding="utf-8")


def parse_doc(path):
    return BeautifulSoup(read(path), "html.parser")


def kids(el):
    return [c for c in el.children if isinstance(c, Tag)]


def fmt_pct(v):
    return f"{round(float(v) * 100, 4):g}%"


def fmt_bar(v):
    return f"{round(float(v), 6):g}"


def style_get(el, prop):
    m = re.search(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)", el.get("style") or "")
    return m.group(1).strip() if m else None


def style_set(el, prop, value):
    style = el.get("style") or ""
    pattern = rf"((?:^|;)\s*{re.escape(prop)}\s*:\s*)[^;]+"
    if re.search(pattern, style):
        el["style"] = re.sub(pattern, lambda m: m.group(1) + value, style, count=1)
    else:
        el["style"] = (style.rstrip(";") + ";" if style else "") + f"{prop}:{value}"


def in_repeat(el):
    return el.find_parent(attrs={"data-repeat": True}) is not None


def in_optional(el):
    return el.find_parent(attrs={"data-optional": True}) is not None


def el_path(root, el):
    """Structural path of el under root as a tuple of child indices."""
    path = []
    node = el
    while node is not root:
        parent = node.parent
        path.append(kids(parent).index(node))
        node = parent
    return tuple(reversed(path))


def at_path(root, path):
    node = root
    for i in path:
        node = kids(node)[i]
    return node


def walk_pairs(a, b):
    """Yield structurally-parallel element pairs of two trees (best effort)."""
    yield a, b
    ka, kb = kids(a), kids(b)
    if len(ka) == len(kb):
        for x, y in zip(ka, kb):
            if x.name == y.name:
                yield from walk_pairs(x, y)


def set_text(el, value):
    for c in list(el.children):
        c.extract()
    el.append(value)


# Renderer control attributes have no legitimate use inside content-supplied
# html fragments (prose with inline emphasis spans). Stripping them at insert
# time means content can never smuggle a scan exemption, a fake banned-list
# wrapper, or slot/repeat machinery into a rendered document and past
# verify's exclusions (F1, 1.0.2 advisor finding).
CONTENT_STRIPPED_ATTRS = ("data-verify-exempt", "data-repeat", "data-slot",
                          "data-bar", "data-count", "data-optional")


def build_nested_slot_map(soup):
    """Template-anchored, PER-SLOT keep-set for set_html(): for every
    data-slot name S found in the bound TEMPLATE itself (soup, parsed fresh
    and not yet mutated), the set of data-slot names that appear among S's
    OWN descendants there (unioned across every place S's name recurs, e.g.
    repeated rows -- structurally identical instances agree). A schema-wide
    allowed set was wrong: it let a fragment filling slot A carry a
    data-slot naming a DIFFERENT real slot B, which extract's later-wins
    layout scan then rebound onto B's own (sibling) element on the next
    render -- confirmed exploits: TK_08's story.prompts row html
    (prompt.listen) smuggling <span data-slot="prompt.text"> shadowed the
    row's real prompt.text; a doc.thesis fragment smuggling
    data-slot="footer.right" produced two footer.right elements. Keying by
    S's own nested set closes this by construction: TK_08's sell.script
    legitimately nests sell.date, so "sell.date" in
    nested_map["sell.script"], but prompt.listen nests nothing and
    doc.thesis nests nothing, so those smuggled names never match their
    OWN slot's set and are stripped like any other control attribute,
    regardless of what any other slot in the template legitimately
    declares. Every non-data-slot CONTENT_STRIPPED_ATTRS attribute is still
    stripped unconditionally in set_html() -- this buys no verify
    exemption; verify's own exemption check stays separately
    template-anchored (see tpl_exempt in verify())."""
    nested = {}
    for el in soup.find_all(attrs={"data-slot": True}):
        name = el["data-slot"]
        names = {d["data-slot"] for d in el.find_all(attrs={"data-slot": True})}
        nested.setdefault(name, set()).update(names)
    return nested


def set_html(el, fragment, allowed_slots=None):
    """allowed_slots: the CALLER-resolved keep-set for the specific slot
    being filled (build_nested_slot_map()[that slot's own name]), never a
    schema-wide set -- see build_nested_slot_map for why that distinction
    is the whole fix."""
    for c in list(el.children):
        c.extract()
    frag = BeautifulSoup(fragment, "html.parser")
    allowed = allowed_slots or frozenset()
    for t in frag.find_all(True):
        for a in CONTENT_STRIPPED_ATTRS:
            if not t.has_attr(a):
                continue
            if a == "data-slot" and t[a] in allowed:
                continue  # nested inside THIS slot in the template itself:
                          # a legitimate nested slot, not smuggled machinery.
            del t[a]
    for node in list(frag.children):
        el.append(node)


def clean_text(el):
    return re.sub(r"\s+", " ", el.get_text()).strip()


# ---------------------------------------------------------------- bar geometry


def bar_form(el):
    style = el.get("style") or ""
    if "conic-gradient" in style:
        return "donut"
    raw = (el.get("data-bar") or "").strip()
    if "," in raw:
        return "range"
    if style_get(el, "left") is not None and style_get(el, "width") is not None:
        return "range"
    return "width"


def apply_bar(el, value, report):
    """value: number, [a,b], or 'a,b' string. Rewrites data-bar + inline geometry."""
    form = bar_form(el)
    if isinstance(value, str) and "," in value:
        value = [float(x) for x in value.split(",")]
    if form == "range":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            report["errors"].append(
                f"bar on <{el.name}> expects [start,end], got {value!r}")
            return
        a, b = float(value[0]), float(value[1])
        el["data-bar"] = f"{fmt_bar(a)},{fmt_bar(b)}"
        style_set(el, "left", fmt_pct(a))
        style_set(el, "width", fmt_pct(b - a))
    elif form == "donut":
        v = float(value if not isinstance(value, (list, tuple)) else value[0])
        el["data-bar"] = fmt_bar(v)
        pct = fmt_pct(v)
        style = el.get("style") or ""
        new = re.sub(
            r"conic-gradient\(\s*([^,]+?)\s+0%?\s+[\d.]+%\s*,\s*([^,]+?)\s+[\d.]+%\s+100%\s*\)",
            lambda m: f"conic-gradient({m.group(1)} 0 {pct}, {m.group(2)} {pct} 100%)",
            style)
        if new == style:
            new = re.sub(
                r"conic-gradient\(\s*([^,]+?)\s+0\s+[\d.]+%\s*,\s*([^,]+?)\s+[\d.]+%\s+100%\s*\)",
                lambda m: f"conic-gradient({m.group(1)} 0 {pct}, {m.group(2)} {pct} 100%)",
                style)
        if new == style:
            report["errors"].append("donut conic-gradient not rewritable: " + style[:80])
        el["style"] = new
    else:
        v = float(value if not isinstance(value, (list, tuple)) else value[0])
        el["data-bar"] = fmt_bar(v)
        style_set(el, "width", fmt_pct(v))


def read_bar(el):
    raw = (el.get("data-bar") or "").strip()
    if "," in raw:
        return [float(x) for x in raw.split(",")]
    try:
        return float(raw)
    except ValueError:
        return raw


# ---------------------------------------------------------------- schema build


def struct_sig(el):
    return (el.name, tuple(struct_sig(k) for k in kids(el)))


def grid_cols(container):
    g = style_get(container, "grid-template-columns") or ""
    total = 0
    toks = re.findall(r"repeat\(\s*(\d+)\s*,[^)]*\)|(\S+)", g)
    for rep, plain in toks:
        total += int(rep) if rep else 1
    return total


def classify_repeat(container):
    ks = kids(container)
    if not ks:
        return {"kind": "rows"}
    style = container.get("style") or ""
    if "display:grid" in style.replace(" ", "") and any(
            (k.get("style") or "").find("min-height") >= 0 and not clean_text(k)
            for k in ks):
        return {"kind": "grid", "cols": grid_cols(container)}
    first = ks[0]
    if style_get(first, "left") and style_get(first, "top") and \
            "absolute" in (style_get(first, "position") or ""):
        return {"kind": "points"}
    return {"kind": "rows"}


def row_slot_layout(row):
    """Map slot name -> structural path within the row (row itself = ())."""
    layout = {}
    if row.has_attr("data-slot"):
        layout[row["data-slot"]] = ()
    for el in row.find_all(attrs={"data-slot": True}):
        nested = el.find_parent(attrs={"data-repeat": True})
        if nested is not None and nested in row.descendants:
            continue  # belongs to a nested repeat
        layout[el["data-slot"]] = el_path(row, el)
    return layout


def direct_text(el):
    """Concatenated text of el's own text-node children (not descendants).
    HTML comments (e.g. "<!-- 01 · WHY OUTBOUND -->" section annotations) are
    NavigableString too but are not content; they are excluded."""
    return re.sub(r"\s+", " ", "".join(
        str(c) for c in el.children
        if not isinstance(c, Tag) and not isinstance(c, Comment))).strip()


def unslotted_text_paths(row, layout):
    """Paths of elements carrying template-positional text: direct text present,
    no data-slot of their own, path not already a slot target, and not nested
    inside another slot's own subtree (a <span> commentary aside inside a
    data-slot <td> is part of that slot's own value, per slot_value_of's
    clean_text() merge and fill_slot_value's set_text() overwrite; it is not
    independent unslotted content and must not be double-claimed). A row-level
    slot (data-slot on the row itself, path == ()) covers the WHOLE row, so
    p[:0] == () must match every descendant path too: `sp`'s truthiness must
    not suppress that just because () is falsy (F2 fix -- without this, a
    whole-row html slot like TK_01's layer.owned left its own inner prose
    looking "unslotted" and spawned a redundant synthetic slot nested inside
    the very html blob that already carries it; that duplicate is fragile the
    moment the filled html isn't exactly the example's two top-level tags,
    see stack.layers.v1.prose0)."""
    slot_paths = set(layout.values())
    paths = []
    for el in row.find_all(True):
        nested = el.find_parent(attrs={"data-repeat": True})
        if nested is not None and nested in row.descendants:
            continue
        p = el_path(row, el)
        if p in slot_paths or el.has_attr("data-slot"):
            continue
        if any(p[:len(sp)] == sp for sp in slot_paths):
            continue
        if direct_text(el):
            paths.append(p)
    return paths


def synthetic_row_entries(row, layout, siblings, name_prefix):
    """Build synthetic slot entries for unslotted direct-text paths in `row`
    (relative to `row`) whose text is worked-example prose (>= MIN_SYNTHETIC_LEN
    chars) either in `row` itself or in any `siblings` row that shares the same
    shape/paths (the base row's positional clones: a later worked-example row
    can carry much longer text at a path than the base row does, which is
    exactly how the propulsion prose survived undetected before this fix).
    Name convention: f"{name_prefix}.prose{i}" in document order."""
    entries = {}
    idx = 0
    for p in unslotted_text_paths(row, layout):
        texts = [direct_text(at_path(row, p))]
        for sib in siblings:
            try:
                texts.append(direct_text(at_path(sib, p)))
            except (IndexError, TypeError):
                continue
        longest = max(texts, key=len)
        if len(longest) >= MIN_SYNTHETIC_LEN:
            sname = f"{name_prefix}.prose{idx}"
            idx += 1
            entries[sname] = {"type": "prose_long", "synthetic": True,
                               "path": list(p), "example": longest[:220]}
    return entries


def doc_synthetic_slots(soup):
    """Synthetic slots for unslotted direct text >= MIN_SYNTHETIC_LEN outside
    any data-repeat / data-optional block, anywhere in the document. Named
    doc.prose0, doc.prose1, ... in document order."""
    entries = {}
    idx = 0
    for el in soup.find_all(True):
        if el.name in ("script", "style"):
            continue
        if el.has_attr("data-slot") or in_repeat(el) or in_optional(el):
            continue
        if el.find_parent(attrs={"data-slot": True}) is not None:
            continue  # nested inside a real slot's own subtree: that slot's
                       # value already carries this text, see slot_value_of.
        t = direct_text(el)
        if len(t) >= MIN_SYNTHETIC_LEN_DOC:
            sname = f"doc.prose{idx}"
            idx += 1
            entries[sname] = {"type": "prose_long", "synthetic": True,
                               "path": list(el_path(soup, el)), "example": t[:220]}
    return entries


def match_synthetic(info, layout):
    """Given a repeat's schema info and the REAL (attribute-based) slot layout
    a rendered/extracted row is actually using, return {synthetic_name: path}
    for whichever row shape (base or a row_variant) that layout matches. Real
    slot names are stable structural fingerprints: row_slot_layout() already
    keys rows by their own data-slot names, so comparing that name-set against
    the schema's recorded name-set (minus synthetic entries) identifies which
    shape produced this row, without needing any position bookkeeping."""
    if not info:
        return {}
    row_slots = info.get("row_slots", {})
    real_base = {n for n, e in row_slots.items() if not e.get("synthetic")}
    if set(layout.keys()) == real_base:
        return {n: e["path"] for n, e in row_slots.items() if e.get("synthetic")}
    for variant in info.get("row_variants", []):
        vslots = variant.get("row_slots", {})
        real_v = {n for n, e in vslots.items() if not e.get("synthetic")}
        if set(layout.keys()) == real_v:
            return {n: e["path"] for n, e in vslots.items() if e.get("synthetic")}
    return {}


def fill_synthetic(root, path, key, values, report, report_name=None):
    """Fill (or, per the F1 safety rule, BLANK) one synthetic prose slot.
    Missing content NEVER leaves template example prose behind: it blanks the
    element's direct text and records the slot as missing instead."""
    report_name = report_name or key
    try:
        el = at_path(root, tuple(path))
    except (IndexError, TypeError):
        report["errors"].append(f"synthetic slot {report_name}: path not resolvable")
        return
    if key in values and values[key] is not None:
        set_direct_text(el, str(values[key]))
    else:
        # A JSON null is a legal value form per shared core §5.2; without the
        # is-not-None guard it rendered the literal string "None" at exit 0,
        # invisible to verify (--strict does not close that hole either).
        # Blank-and-report, same as an absent key.
        set_direct_text(el, "")
        report["missing"].append(report_name)


def set_direct_text(el, value):
    """Replace only el's own text-node children, keeping element children."""
    for c in list(el.children):
        if not isinstance(c, Tag):
            c.extract()
    el.append(value)


def parse_pill_text(text):
    """'Sourced · BLS-OES 2024' -> {'pill': 'Sourced', 'method': 'BLS-OES 2024'}."""
    head, _, rest = text.partition(" · ")
    if head in PILL_STYLES:
        return {"pill": head, **({"method": rest} if rest else {})}
    return None


def slot_value_of(el, sname):
    """Extract a content value from a filled slot element."""
    ekids = kids(el)
    if len(ekids) > 1:
        return {"html": "".join(str(k) for k in ekids)}
    text = clean_text(el)
    if sname.endswith(".pill"):
        parsed = parse_pill_text(text)
        if parsed:
            return parsed
    if el.name == "span" and text in PILL_STYLES:
        return {"pill": text}
    return text


def row_bar_paths(row):
    paths = []
    if row.has_attr("data-bar"):
        paths.append(())
    for el in row.find_all(attrs={"data-bar": True}):
        nested = el.find_parent(attrs={"data-repeat": True})
        if nested is not None and nested in row.descendants:
            continue
        paths.append(el_path(row, el))
    return paths


def build_schema(template_path, slot_types_path=None):
    soup = parse_doc(template_path)
    types = {}
    if slot_types_path:
        st = json.loads(read(slot_types_path))
        types = {k: v.get("type") for k, v in st.get("slots", {}).items()}
    words = {}
    if slot_types_path:
        words = {k: v.get("words") for k, v in st.get("slots", {}).items()}

    schema = {"template": Path(template_path).name, "version": "1.0",
              "slots": {}, "repeats": {}, "standalone_bars": [],
              "optionals": [], "toggles": [], "handoff_slots": []}

    for el in soup.find_all(attrs={"data-slot": True}):
        name = el["data-slot"]
        if in_repeat(el) or in_optional(el):
            continue
        if name.startswith("handoff."):
            schema["handoff_slots"].append(name)
            continue
        entry = {"type": types.get(name, "label")}
        if words.get(name):
            entry["words"] = words[name]
        ekids = kids(el)
        if len(ekids) > 1:
            entry["html"] = True
        entry["example"] = clean_text(el)[:160]
        schema["slots"][name] = entry

    # Synthetic slots (F1): unslotted direct text >= MIN_SYNTHETIC_LEN chars,
    # anywhere in the document outside a data-repeat or data-optional block.
    # Listed alongside real top-level slots so content agents discover and
    # fill them the same way ("fill schema-listed synthetic prose slots like
    # any other slot").
    schema["slots"].update(doc_synthetic_slots(soup))

    for container in soup.find_all(attrs={"data-repeat": True}):
        if container.find_parent(attrs={"data-repeat": True}) is not None:
            continue  # nested repeats are described inside their parent row
        name = container["data-repeat"]
        info = classify_repeat(container)
        info["count"] = container.get("data-count", "")
        info["optional_block"] = in_optional(container)
        ks = kids(container)
        if info["kind"] == "rows" and ks:
            first = ks[0]
            layout = row_slot_layout(first)
            info["row_slots"] = {
                s: {"type": types.get(s, "label"),
                    **({"words": words[s]} if words.get(s) else {})}
                for s in layout}
            # Synthetic slots (F1): unslotted direct text in the base row that
            # is worked-example prose. A "positional" sibling (a later example
            # row with no data-slot of its own, cloned by copying its text
            # onto the base's structure at render time, see render_rows) can
            # carry far longer text at the same structural path than the base
            # row does, so every positional sibling is sampled too.
            positional_siblings = [k for k in ks[1:] if not row_slot_layout(k)]
            info["row_slots"].update(
                synthetic_row_entries(first, layout, positional_siblings, name))
            info["bars_per_row"] = len(row_bar_paths(first))
            if info["bars_per_row"]:
                forms = []
                for p in row_bar_paths(first):
                    forms.append(bar_form(at_path(first, p)))
                info["bar_forms"] = forms
            nested = [r["data-repeat"] for r in first.find_all(attrs={"data-repeat": True})]
            if nested:
                info["nested"] = {}
                for nname in nested:
                    ncont = first.find(attrs={"data-repeat": nname})
                    nks = kids(ncont)
                    nlayout = row_slot_layout(nks[0]) if nks else {}
                    info["nested"][nname] = {
                        "count": ncont.get("data-count", ""),
                        "row_slots": {s: {"type": types.get(s, "label")} for s in nlayout}}
            info["example_rows"] = len(ks)
            # Distinct row variants: later example rows carrying their own slot
            # attributes are separate card types, matched to content BY POSITION.
            variants = []
            for vi, vk in enumerate(ks[1:], 1):
                vlayout = row_slot_layout(vk)
                if vlayout:
                    vrow_slots = {s: {"type": types.get(s, "label")} for s in vlayout}
                    vrow_slots.update(
                        synthetic_row_entries(vk, vlayout, [], f"{name}.v{vi}"))
                    variants.append({
                        "position": vi,
                        "row_slots": vrow_slots,
                        "bars_per_row": len(row_bar_paths(vk)),
                        "nested": [r["data-repeat"] for r in
                                   vk.find_all(attrs={"data-repeat": True})]})
            if variants:
                info["row_variants"] = variants
        elif info["kind"] == "grid" and ks:
            cols = info["cols"]
            n_data = cols - 1
            info["data_cols"] = n_data
            info["header_examples"] = [clean_text(k) for k in ks[1:1 + n_data]]
            info["cell_vocab"] = sorted(HEAT_STRENGTH.keys())
            label_slot = None
            for k in ks[1 + n_data:]:
                if k.has_attr("data-slot"):
                    label_slot = k["data-slot"]
                    break
            info["label_slot"] = label_slot or "heat.label"
            info["example_rows"] = (len(ks) - 1 - n_data) // (1 + n_data)
        elif info["kind"] == "points" and ks:
            first = ks[0]
            layout = row_slot_layout(first)
            info["label_slot"] = next(iter(layout), "point.label")
            info["example_rows"] = len(ks)
        schema["repeats"][name] = info

    for el in soup.find_all(attrs={"data-bar": True}):
        if in_repeat(el) or in_optional(el):
            continue
        schema["standalone_bars"].append({
            "form": bar_form(el), "example": read_bar(el),
            "context": clean_text(el.parent)[:80]})

    for i, el in enumerate(soup.find_all(attrs={"data-optional": True}), 1):
        oslots = {}
        has_handoff = False
        candidates = ([el] if el.has_attr("data-slot") else []) + \
            el.find_all(attrs={"data-slot": True})
        for s in candidates:
            if s["data-slot"].startswith("handoff."):
                has_handoff = True
                continue
            oslots[s["data-slot"]] = {"type": types.get(s["data-slot"], "label")}
        oreps = [r["data-repeat"] for r in el.find_all(attrs={"data-repeat": True})]
        schema["optionals"].append({"id": f"optional_{i}", "slots": oslots,
                                    "repeats": oreps,
                                    "handoff_block": has_handoff,
                                    "context": clean_text(el)[:100]})

    m = re.search(r"state\s*=\s*\{([^}]*)\}", str(soup))
    if m:
        schema["toggles"] = re.findall(r"(\w+)\s*:", m.group(1))

    return schema


# ---------------------------------------------------------------- template lint

# RISKY text on the verbatim-copy surface: currency amounts, standalone
# K-figures, thousands-separated numbers, percentile tokens, percentages,
# 4-digit years, and month names. This is a lint, not a parser -- patterns
# are loose on purpose. A false negative here is exactly how the propulsion
# demo's '$66-83K' and '105k' axis ticks shipped into a client document
# undetected; a false positive just costs one review.
_LINT_MONTHS = (
    r"january|february|march|april|may|june|july|august|september|october"
    r"|november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec")
RISKY_TEXT_PATTERN = re.compile(
    r"[$€£]\s?\d"                                    # currency amount
    r"|\b\d[\d,]*\s?[Kk]\b"                          # standalone K-figure
    r"|\b\d[\d,]*(?:\.\d+)?\s?[Mm]\b"                # standalone M-figure (millions)
    r"|\b\d{1,3}(?:,\d{3})+\b"                       # thousands-separated number
    r"|\b\d{6,}\b"                                   # bare 6+ digit figure (e.g. "120000")
    r"|\bP\d{2}\b"                                   # percentile token (P25, P90)
    r"|\d+(?:\.\d+)?\s?%"                             # percentage
    r"|\b(?:19|20)\d{2}\b"                           # 4-digit year
    rf"|\b(?:{_LINT_MONTHS})\b\.?\s+\d{{1,2}}\b"      # month + day ("March 14")
    rf"|\b(?:{_LINT_MONTHS})\b\.?\s+(?:19|20)\d{{2}}\b",  # month + year
    re.I)


def _has_synthetic_pass(container):
    """True iff `container` (a data-repeat) is the one build_schema()
    describes AND render() actually threads that schema info into
    render_rows() for it -- i.e. it is not nested inside another
    data-repeat and not inside a data-optional block. render()'s nested-
    repeat call (render_rows(ncont, ndata, {}, ...)) and its optional-pass
    call (render_rows(cont, rdata, {}, ...)) both hardcode info={}, so
    match_synthetic({}, ...) is always {} there: NOTHING on those surfaces
    is ever promoted to a synthetic slot, filled, or blanked, regardless of
    text length -- even though build_schema() (which does not know how
    render() will route the container) may have computed synthetic entries
    for it. The lint must use this REAL predicate, not build_schema's
    length floor, or it exempts text that actually ships verbatim (round-2
    red-team M4)."""
    if container.find_parent(attrs={"data-repeat": True}) is not None:
        return False
    if in_optional(container):
        return False
    return True


def _repeat_risky_texts(container):
    """Enumerate the row-level verbatim-copy surface (a) of `container` (a
    data-repeat, kind=="rows"): every place render_rows either renders
    template text as-is or copies it positionally rather than filling it
    from content. Three row classes, matching render_rows' own dispatch
    (~line 711) and build_schema's synthetic_row_entries sampling of the
    same classes:

      - the base row's (ks[0]) own unslotted text -- rendered as-is for
        row 0, every render, unconditionally;
      - each later "slotless" row (own_layout empty, i.e. it carries none
        of its own data-slot attributes) sampled AT THE BASE ROW'S OWN
        unslotted paths -- render_rows' positional-copy branch (~line 733)
        clones the BASE row's structure and copies text onto it from
        whatever sits at that same structural path in this proto row;
      - each later TRUE variant row (own_layout non-empty -- a distinct
        card type cloned wholesale, e.g. TK_05's voice.blocks) sampled at
        ITS OWN unslotted paths -- render_rows clones it directly and only
        fills its own declared slots, so its own furniture text survives
        exactly like the base row's does.

    Deliberately narrower than "every unslotted text anywhere in the
    repeat's example rows": a slotless row's text at a path base does NOT
    share never reaches a render two ways -- either that base path IS a
    real slot (content overwrites it every time; confirmed on TK_07's
    comp.sources, where every later example row's own text is fully
    replaced because the base row slots all 5 cells) or the path plain
    doesn't exist in base's shape (IndexError below; confirmed on TK_07's
    comp.rows 3rd example row, whose two extra tick divs sit past where
    base's structure ends). A wider scan that ignored this flagged both as
    "risky" and buried the 3 texts that are actually reachable in an avalanche
    of dead template text across every table-shaped repeat in the pack --
    tried, measured, reverted; see the fixer diff notes.

    EXEMPTION (round-2 fix, replaces the old length-floor proxy): a path is
    exempt only if it is ACTUALLY promoted to a synthetic slot at render
    time. That requires (1) `container` has a synthetic pass at all
    (_has_synthetic_pass) and (2) the path is one synthetic_row_entries()
    would emit for the relevant row shape (base shape for row0 and
    positional rows -- sampled across the base row AND every positional
    sibling, exactly like build_schema does, so a short base-row text at a
    path a LONGER sibling promotes is correctly exempt too, matching what
    fill_synthetic actually blanks there; own shape, sampled with no
    siblings, for a true variant row). On a container with no synthetic
    pass (nested repeat, or a repeat inside a data-optional block) nothing
    is ever exempt: every unslotted path is scanned regardless of length,
    because render_rows never promotes anything there (M4).

    Returns [{"path": [...], "text": ..., "row": <source label>}] for every
    unslotted, non-exempt, non-empty text found."""
    ks = kids(container)
    if not ks:
        return []
    base = ks[0]
    base_layout = row_slot_layout(base)
    base_paths = unslotted_text_paths(base, base_layout)
    has_pass = _has_synthetic_pass(container)
    rname = container.get("data-repeat") or "repeat"
    out = []

    if has_pass:
        positional_siblings = [k for k in ks[1:] if not row_slot_layout(k)]
        base_exempt = {tuple(e["path"]) for e in
                        synthetic_row_entries(base, base_layout,
                                              positional_siblings, rname).values()}
    else:
        base_exempt = set()

    def add_if_furniture(path, text, source, exempt):
        if text and tuple(path) not in exempt:
            out.append({"path": list(path), "text": text, "row": source})

    for p in base_paths:
        add_if_furniture(p, direct_text(at_path(base, p)), "row0", base_exempt)

    for i, row in enumerate(ks[1:], 1):
        own_layout = row_slot_layout(row)
        if own_layout:
            if has_pass:
                variant_exempt = {tuple(e["path"]) for e in
                                  synthetic_row_entries(row, own_layout, [],
                                                        f"{rname}.v{i}").values()}
            else:
                variant_exempt = set()
            for p in unslotted_text_paths(row, own_layout):
                add_if_furniture(p, direct_text(at_path(row, p)),
                                 f"row{i}(variant)", variant_exempt)
        else:
            for p in base_paths:
                try:
                    el = at_path(row, p)
                except (IndexError, TypeError):
                    continue  # base's path doesn't exist in this proto's
                              # own shape: render_rows can't reach it either.
                add_if_furniture(p, direct_text(el), f"row{i}(positional)",
                                 base_exempt)
    return out


def _points_risky_texts(container):
    """Enumerate the verbatim-copy surface of a `kind=="points"` data-repeat:
    render_points() ALWAYS clones the base row (ks[0]) -- `clone =
    copy.copy(base)` runs unconditionally for every rendered point, later
    protos only donate inline STYLE via patch_styles(), never text -- and
    only ever set_text()s ONE element, the label-slot target (or, absent a
    data-slot, its own positional fallback: the last non-dot <span>, or the
    row itself if there are no spans at all). Every other text node in the
    base row, at ANY length, clones onto every rendered point verbatim
    (round-2 red-team M1) -- there is no synthetic-slot pass for points at
    all, so no length floor ever applied here validly."""
    ks = kids(container)
    if not ks:
        return []
    base = ks[0]
    layout = row_slot_layout(base)
    label_slot = next(iter(layout), "point.label")
    target = base.find(attrs={"data-slot": label_slot})
    if target is None:
        # Mirrors render_points' own fallback exactly: last non-dot <span>,
        # or the row itself if there are no spans (in which case set_text()
        # wipes the row's ENTIRE subtree, so nothing survives -- correctly
        # nothing to flag).
        dot = None
        for sp in base.find_all("span"):
            if style_get(sp, "border-radius"):
                dot = sp
                break
        spans = [s for s in base.find_all("span") if s is not dot]
        target = spans[-1] if spans else base
    target_path = () if target is base else el_path(base, target)
    out = []
    candidates = [(base, ())] + [(el, el_path(base, el)) for el in base.find_all(True)]
    for el, p in candidates:
        if p[:len(target_path)] == target_path:
            continue  # the label target itself (or its own subtree): the
                       # one thing render_points actually overwrites.
        t = direct_text(el)
        if t:
            out.append({"path": list(p), "text": t, "row": "row0"})
    return out


def _grid_corner_texts(container):
    """Enumerate the verbatim-copy surface of a `kind=="grid"` data-repeat's
    corner cell: render_grid() clones ks[0] with `copy.copy(corner)` and
    appends it unmodified -- it is never set_text()d or otherwise touched --
    so every bit of text anywhere inside it, at ANY length, ships verbatim
    on every render regardless of content (round-2 red-team M2)."""
    ks = kids(container)
    if not ks:
        return []
    corner = ks[0]
    out = []
    t = direct_text(corner)
    if t:
        out.append({"path": [], "text": t, "row": "corner"})
    for el in corner.find_all(True):
        t = direct_text(el)
        if t:
            out.append({"path": list(el_path(corner, el)), "text": t, "row": "corner"})
    return out


def _optional_block_texts(opt_el):
    """Enumerate the verbatim-copy surface of a data-optional block's own
    unslotted direct text (outside any nested data-repeat, which is scanned
    separately, per-container, by the row/points/grid scans above): render()
    only ever fill_slot_value()s the optional's OWN declared data-slot
    elements and render_rows()s its OWN declared data-repeat containers --
    everything else in the block is appended to the document completely
    unmodified whenever the optional is provided. build_schema() never
    creates a synthetic slot for optional-block content at all (its
    doc_synthetic_slots() walk explicitly excludes in_optional() elements),
    so nothing here is EVER promoted: every unslotted path is verbatim
    surface at ANY length (round-2 red-team M3). unslotted_text_paths()
    already gives us exactly this -- treating the optional element like a
    "row" whose own layout is its own (non-repeat-nested) data-slot set --
    including the existing nested-repeat exclusion, so a repeat inside the
    optional is not double-counted here."""
    layout = row_slot_layout(opt_el)
    out = []
    for p in unslotted_text_paths(opt_el, layout):
        t = direct_text(at_path(opt_el, p))
        if t:
            out.append({"path": list(p), "text": t})
    return out


def _attribute_risky_texts(soup):
    """Attribute-borne text (title / alt / aria-label): none of the checks
    above -- or verify()'s text-node scans -- ever look at attribute values
    (clean_text()/get_text() only see element content), so a risky or
    domain-marker figure baked into an attribute ships silently regardless
    of slot/repeat/optional context; there is no promotion mechanism for
    attributes at all. Informational tier (SHOULD-FIX, not a MUST-FIX
    silent-miss class) -- see verify()'s severity split."""
    out = []
    for el in soup.find_all(True):
        if el.name in ("script", "style"):
            continue
        for attr in ("title", "alt", "aria-label"):
            v = (el.get(attr) or "").strip()
            if v:
                out.append({"path": list(el_path(soup, el)), "attr": attr, "text": v})
    return out


def lint_template(template_path):
    """Template-furniture lint: enumerate the verbatim-copy surface this
    module ships (see MIN_SYNTHETIC_LEN / MIN_SYNTHETIC_LEN_DOC) and flag
    entries whose text matches RISKY_TEXT_PATTERN or DOMAIN_MARKERS -- the
    surface class that let propulsion-demo comp figures ('$66-83K', '105k'
    axis ticks) ship into a client JD/calibration brief unnoticed, because
    that text is never a real data-slot and never long enough to become a
    synthetic one, so nothing before this lint ever looked at it.

    Six surfaces:
      (a) row-level, via _repeat_risky_texts() on every data-repeat whose
          kind is "rows", exempting exactly the paths that container's
          ACTUAL synthetic pass (if it has one at all -- see
          _has_synthetic_pass) promotes, at any length otherwise (round-2:
          MUST-FIX M4/M5 -- replaces the old length-floor proxy, which
          both missed real leaks on nested/optional-pass repeats where
          nothing is ever promoted, and false-positived on short base-row
          text a longer sibling promotes anyway);
      (b) points-level, via _points_risky_texts() on every "points" repeat:
          every non-label text node in the base row, at any length (M1);
      (c) grid-corner, via _grid_corner_texts() on every "grid" repeat's
          corner cell, at any length (M2);
      (d) optional-block, via _optional_block_texts() on every
          data-optional element's own unslotted direct text, at any length
          (M3);
      (e) doc-level, via the same unslotted-text scan doc_synthetic_slots()
          runs, at doc_synthetic_slots' own MIN_SYNTHETIC_LEN_DOC floor
          (unchanged -- doc-level top-level text >= that floor IS actually
          promoted by build_schema/fill_synthetic, so the floor here is the
          correct predicate, not a proxy);
      (f) attribute-borne, via _attribute_risky_texts() -- title / alt /
          aria-label anywhere in the document, at any length. Informational
          tier (SHOULD-FIX): verify() escalates this one to MEDIUM, every
          other surface to HIGH (see verify()).

    Exemptions: text inside a real data-slot (never visited by any scan);
    text at a path an ACTUAL synthetic pass promotes (row-level and
    doc-level only -- see above); the sanctioned footer credit
    (SANCTIONED_CREDIT); and generic captions with no digits and no domain
    marker (RISKY_TEXT_PATTERN / DOMAIN_MARKERS simply don't match
    "typical" or "low end").

    Returns a list of {"surface": "row"|"points"|"grid-corner"|
    "optional-block"|"doc"|"attribute", "repeat": name-or-None,
    "row": source-or-None, "path": [...]-or-None, "text": ...},
    most-specific first."""
    soup = parse_doc(template_path)
    findings = []

    def risky(text):
        if SANCTIONED_CREDIT in text.lower():
            return False
        return bool(RISKY_TEXT_PATTERN.search(text) or DOMAIN_MARKERS.search(text))

    for container in soup.find_all(attrs={"data-repeat": True}):
        rname = container.get("data-repeat")
        kind = classify_repeat(container).get("kind")
        if kind == "rows":
            for item in _repeat_risky_texts(container):
                if risky(item["text"]):
                    findings.append({"surface": "row", "repeat": rname,
                                     "row": item["row"], "path": item["path"],
                                     "text": item["text"]})
        elif kind == "points":
            for item in _points_risky_texts(container):
                if risky(item["text"]):
                    findings.append({"surface": "points", "repeat": rname,
                                     "row": item["row"], "path": item["path"],
                                     "text": item["text"]})
        elif kind == "grid":
            for item in _grid_corner_texts(container):
                if risky(item["text"]):
                    findings.append({"surface": "grid-corner", "repeat": rname,
                                     "row": item["row"], "path": item["path"],
                                     "text": item["text"]})

    # (d) optional-block: every data-optional element's own unslotted
    # direct text (repeats inside it are covered by (a)/(b)/(c) above,
    # each of which already treats an in_optional() container as having no
    # synthetic pass).
    for opt_el in soup.find_all(attrs={"data-optional": True}):
        for item in _optional_block_texts(opt_el):
            if risky(item["text"]):
                findings.append({"surface": "optional-block", "repeat": None,
                                 "row": "block", "path": item["path"],
                                 "text": item["text"]})

    # (e) doc-level: same walk as doc_synthetic_slots(), same exclusions,
    # just a floor comparison (< MIN_SYNTHETIC_LEN_DOC, the text
    # doc_synthetic_slots would NOT have promoted to a slot) instead of a
    # synthetic-slot-creation threshold.
    for el in soup.find_all(True):
        if el.name in ("script", "style"):
            continue
        if el.has_attr("data-slot") or in_repeat(el) or in_optional(el):
            continue
        if el.find_parent(attrs={"data-slot": True}) is not None:
            continue
        t = direct_text(el)
        if t and len(t) < MIN_SYNTHETIC_LEN_DOC and risky(t):
            findings.append({"surface": "doc", "repeat": None, "row": None,
                             "path": list(el_path(soup, el)), "text": t})

    # (f) attribute-borne (SHOULD-FIX, informational tier -- see verify()).
    for item in _attribute_risky_texts(soup):
        if risky(item["text"]):
            findings.append({"surface": "attribute", "repeat": None,
                             "row": item["attr"], "path": item["path"],
                             "text": item["text"]})

    return findings


def _format_lint_finding(w):
    """One-line human-readable rendering of a lint_template() finding, used
    both for schema's stderr warning and verify()'s finding evidence, so
    the two surfaces never describe the same finding two different ways."""
    if w.get("repeat"):
        where = f"{w['repeat']}[{w['row']}]"
    elif w.get("surface") == "optional-block":
        where = "optional-block"
    elif w.get("surface") == "attribute":
        where = f"attribute:{w['row']}"
    else:
        where = "doc"
    return f"{where} path={w['path']}: {w['text'][:70]!r}"


# ---------------------------------------------------------------- render


def fill_slot_value(el, value, report, name, allowed_slots=None):
    if value is None:
        target = el
        node = el.parent
        while node is not None and node.name not in ("body", "main", "html"):
            others = [s for s in node.find_all(attrs={"data-slot": True}) if s is not el]
            reps = node.find_all(attrs={"data-repeat": True})
            if others or reps or (isinstance(node, Tag) and node.has_attr("data-slot") and node is not el):
                break
            target = node
            node = node.parent
        report["deleted_slots"].append(name)
        target.extract()
        return
    if isinstance(value, dict) and "pill" in value:
        flavor = value["pill"]
        if flavor not in PILL_STYLES:
            report["errors"].append(f"slot {name}: unknown pill {flavor!r}")
            return
        for prop, val in PILL_STYLES[flavor].items():
            style_set(el, prop, val)
        text = flavor + (f" · {value['method']}" if value.get("method") else "")
        set_text(el, text)
        return
    if isinstance(value, dict) and "html" in value:
        set_html(el, value["html"], allowed_slots)
        return
    set_text(el, str(value))


def patch_styles(target, source):
    for a, b in walk_pairs(target, source):
        if b.has_attr("style"):
            a["style"] = b["style"]
        elif a.has_attr("style"):
            del a["style"]


def render_rows(container, rows, info, report, rname, nested_map=None):
    """nested_map: build_nested_slot_map(soup) from the whole bound template,
    threaded through unchanged; resolved to the CURRENT slot's own keep-set
    at each fill_slot_value call below (nested_map.get(sname, ...)), never
    flattened -- see build_nested_slot_map."""
    protos = kids(container)
    if not protos:
        report["errors"].append(f"repeat {rname}: no example rows in template")
        return
    base = protos[0]
    base_layout = row_slot_layout(base)
    new_rows = []
    for i, row in enumerate(rows):
        proto = protos[min(i, len(protos) - 1)]
        own_layout = row_slot_layout(proto)
        if proto is base or own_layout:
            # Homogeneous first row, or a distinct variant carrying its own
            # slot attributes (e.g. TK_05 voice cards): clone it wholesale.
            clone = copy.copy(proto)
            layout = own_layout
            barpaths = row_bar_paths(proto)
        else:
            # Slotless positional example row: clone the slotted first row,
            # then carry the example row's styles and positional text.
            clone = copy.copy(base)
            layout = base_layout
            barpaths = row_bar_paths(base)
            patch_styles(clone, proto)
            synth_paths = {tuple(p) for p in match_synthetic(info, layout).values()}
            for p in unslotted_text_paths(base, base_layout):
                if p in synth_paths:
                    continue  # >= MIN_SYNTHETIC_LEN text: filled/blanked below,
                              # never copied straight from the template example.
                try:
                    src_el = at_path(proto, p)
                    dst_el = at_path(clone, p)
                except (IndexError, TypeError):
                    continue
                t = direct_text(src_el)
                if t and len(t) < MIN_SYNTHETIC_LEN:
                    set_direct_text(dst_el, t)
        for sname, path in layout.items():
            if sname in row:
                fill_slot_value(at_path(clone, path), row[sname], report,
                                f"{rname}[{i}].{sname}",
                                (nested_map or {}).get(sname, frozenset()))
            else:
                # Same F1 safety rule as fill_synthetic/fill_handoff/the
                # top-level slots loop: missing content NEVER leaves
                # template example prose behind. Round-2 fix (M7, all three
                # red-teams): this branch previously reported the miss but
                # left the clone's element untouched, so a row missing a
                # key kept rendering the BASE row's own worked-example text
                # (identical every time, since clone was copied from the
                # same proto) -- silent on a non-strict render, and even
                # --strict only fails the render code path, it doesn't stop
                # someone from reading the .failed artifact. Blank only the
                # element's own direct text (set_direct_text, not
                # set_text): a row slot MAY legitimately nest another real
                # slot inside its own subtree (build_nested_slot_map), and
                # a full child-wipe here would destroy that nested slot's
                # element before it ever gets its own chance to fill.
                set_direct_text(at_path(clone, path), "")
                report["missing"].append(f"{rname}[{i}].{sname}")
        for sname, spath in match_synthetic(info, layout).items():
            fill_synthetic(clone, spath, sname, row, report,
                            report_name=f"{rname}[{i}].{sname}")
        bars = row.get("bars")
        if bars is None and "bar" in row:
            bars = [row["bar"]]
        if barpaths:
            if bars is None or len(bars) != len(barpaths):
                report["errors"].append(
                    f"repeat {rname} row {i}: needs {len(barpaths)} bar value(s), got {bars!r}")
            else:
                for path, val in zip(barpaths, bars):
                    apply_bar(at_path(clone, path), val, report)
        for ncont in list(clone.find_all(attrs={"data-repeat": True})):
            if ncont.find_parent(attrs={"data-repeat": True}) is not None:
                continue  # deeper nesting handled by recursion
            nname = ncont["data-repeat"]
            ndata = row.get(nname) or []
            if not ndata:
                ncont.extract()
                report["deleted"].append(f"{rname}[{i}].{nname}")
            else:
                render_rows(ncont, ndata, {}, report, f"{rname}.{nname}",
                            nested_map)
        new_rows.append(clone)
    for k in list(container.children):
        k.extract()
    for r in new_rows:
        container.append(r)
        container.append("\n")


def render_grid(container, data, info, report, rname):
    ks = kids(container)
    n_data = info["data_cols"]
    corner, headers = ks[0], ks[1:1 + n_data]
    label_proto = ks[1 + n_data]
    cell_proto = ks[2 + n_data]
    cols = data.get("columns", [])
    rows = data.get("rows", [])
    if len(cols) != n_data:
        report["errors"].append(
            f"grid {rname}: template has {n_data} columns, content has {len(cols)}")
        return
    new = [copy.copy(corner)]
    for c in cols:
        h = copy.copy(headers[0])
        set_text(h, str(c))
        new.append(h)
    for i, row in enumerate(rows):
        lab = copy.copy(label_proto)
        if lab.has_attr("data-slot"):
            pass
        set_text(lab, str(row.get("label", "")))
        new.append(lab)
        cells = row.get("cells", [])
        if len(cells) != n_data:
            report["errors"].append(
                f"grid {rname} row {i}: needs {n_data} cells, got {len(cells)}")
            cells = (cells + ["none"] * n_data)[:n_data]
        for cv in cells:
            cell = copy.copy(cell_proto)
            spec = HEAT_STRENGTH.get(str(cv))
            if spec is None:
                report["errors"].append(f"grid {rname} row {i}: unknown cell {cv!r}")
                spec = HEAT_STRENGTH["none"]
            if cell.has_attr("data-bar"):
                del cell["data-bar"]
            if spec["bar"] is not None:
                cell["data-bar"] = spec["bar"]
            style_set(cell, "background", spec["background"])
            style = cell.get("style") or ""
            style = re.sub(r"(?:^|;)\s*outline\s*:[^;]+", "", style).strip(";")
            cell["style"] = style
            if spec["outline"]:
                style_set(cell, "outline", spec["outline"])
            set_text(cell, "")
            new.append(cell)
    for k in list(container.children):
        k.extract()
    for n in new:
        container.append(n)
        container.append("\n")


def render_points(container, rows, info, report, rname):
    protos = kids(container)
    base = protos[0]
    label_slot = info.get("label_slot", "point.label")
    new = []
    for i, row in enumerate(rows):
        clone = copy.copy(base)
        if i > 0 and len(protos) > 1:
            patch_styles(clone, protos[min(i, len(protos) - 1)])
        style_set(clone, "left", fmt_pct(row["x"]))
        style_set(clone, "top", fmt_pct(row["y"]))
        dot = None
        for sp in clone.find_all("span"):
            if style_get(sp, "border-radius"):
                dot = sp
                break
        if dot is not None:
            if "size" in row:
                px = f"{int(row['size'])}px"
                style_set(dot, "width", px)
                style_set(dot, "height", px)
            style_set(dot, "background",
                      "var(--bh-accent)" if row.get("accent") else "var(--bh-primary)")
        target = clone.find(attrs={"data-slot": label_slot})
        if target is None:
            spans = [s for s in clone.find_all("span") if s is not dot]
            target = spans[-1] if spans else clone
        set_text(target, str(row.get("label", "")))
        new.append(clone)
    for k in list(container.children):
        k.extract()
    for n in new:
        container.append(n)
        container.append("\n")


def remove_repeat_block(container, report, rname):
    prev = container.find_previous_sibling(lambda t: isinstance(t, Tag))
    if prev is not None and prev.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        prev.extract()
        report["deleted"].append(f"heading before {rname}")
    container.extract()
    report["deleted"].append(f"repeat {rname}")


# Every Talent Kit template hand-links Google Fonts directly (2x preconnect +
# 1x stylesheet) as a fallback path separate from the _ds/ hrefs this function
# inlines. tokens.css's --bh-font-* stacks already end in system generics for
# every face those links would load, so stripping them is safe offline and
# keeps the self-contained-output promise honest.
EXTERNAL_FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


def inline_ds(soup, ds_dir, report):
    ds = Path(ds_dir)
    # Strip external font links up front, unconditionally: independent of
    # whether the CSS/JS inlining below succeeds.
    for l in list(soup.find_all("link", href=True)):
        if any(host in l["href"] for host in EXTERNAL_FONT_HOSTS):
            report["warnings"].append(f"stripped external font link: {l['href']}")
            l.extract()
    css_parts = []
    for rel in ("tokens/tokens.css", "styles.css"):
        p = ds / rel
        if not p.exists():
            report["errors"].append(f"design system file missing: {p}")
            return
        text = p.read_text(encoding="utf-8")
        # styles.css opens with @import lines that are correct when the file
        # is linked directly by a browser, but dead once concatenated here:
        # mid-stylesheet @import is invalid CSS (browsers drop it), and the
        # relative path would resolve against the output document anyway.
        # Drop them so no stale reference survives into the render.
        if rel == "styles.css":
            text = re.sub(r'@import\s+"[^"]*"\s*;\s*\n?', "", text)
        css_parts.append(text)
    links = [l for l in soup.find_all("link", rel="stylesheet")
             if "_ds/" in (l.get("href") or "")]
    if links:
        style = soup.new_tag("style")
        style.string = "\n".join(css_parts)
        links[0].replace_with(style)
        for l in links[1:]:
            l.extract()
    bundle = ds / "_ds_bundle.js"
    for s in soup.find_all("script", src=True):
        if "_ds_bundle" in s["src"]:
            js = bundle.read_text(encoding="utf-8") if bundle.exists() else ""
            if not js:
                report["errors"].append(f"missing {bundle}")
            new = soup.new_tag("script")
            new.string = js
            s.replace_with(new)


def apply_toggles(soup, toggles, report):
    if not toggles:
        return
    for script in soup.find_all("script"):
        txt = script.string
        if txt and re.search(r"state\s*=\s*\{", txt):
            def sub_state(m):
                body = m.group(1)
                for name, val in toggles.items():
                    body = re.sub(rf"(\b{re.escape(name)}\s*:\s*)(true|false)",
                                  lambda mm: mm.group(1) + ("true" if val else "false"),
                                  body)
                return "state = {" + body + "}"
            script.string = re.sub(r"state\s*=\s*\{([^}]*)\}", sub_state, txt)
            return
    report["warnings"].append("toggles given but no state literal found")


def fill_handoff(soup, content, artifact, report):
    h = content.get("handoff") or {}
    keys = h.get("keys") or {}
    produces = h.get("produces") or " · ".join(k for k in keys if k != "assumptions")
    values = {
        "handoff.produces": produces or None,
        "handoff.consumers": h.get("consumers") or CONSUMERS.get(artifact) or None,
        "handoff.blocked": h.get("blocked", "Nothing"),
        "handoff.assumptions": h.get("assumptions"),
    }
    for k, v in h.items():
        if k not in ("keys", "produces", "consumers", "blocked", "assumptions"):
            values.setdefault(f"handoff.{k}", v)
    for el in soup.find_all(attrs={"data-slot": True}):
        name = el["data-slot"]
        if not name.startswith("handoff."):
            continue
        v = values.get(name)
        if v is None and name == "handoff.assumptions":
            fill_slot_value(el, None, report, name)
        elif v is None:
            # Same safety rule as synthetic slots: a missing handoff value
            # BLANKS the element. Template example text never survives into a
            # rendered document (1.0.1 live-run finding).
            set_text(el, "")
            report["missing"].append(name)
        else:
            set_text(el, str(v))


def render(template_path, schema, content, ds_dir=None, mode=None, brand=None):
    soup = parse_doc(template_path)
    report = {"errors": [], "warnings": [], "missing": [], "deleted": [],
              "deleted_slots": []}
    # Computed once per render, from the freshly-parsed, still-pristine
    # template soup (before any fill below mutates it): for every slot name,
    # the data-slot names legitimately nested inside THAT slot's own element
    # in the template. See build_nested_slot_map -- this must run before any
    # mutation so it reflects the template's real structure, not a partially
    # filled document.
    nested_map = build_nested_slot_map(soup)

    for name, entry in schema.get("slots", {}).items():
        if entry.get("synthetic"):
            fill_synthetic(soup, entry["path"], name, content.get("slots", {}), report)
            continue
        els = [e for e in soup.find_all(attrs={"data-slot": name})
               if not in_repeat(e) and not in_optional(e)]
        if name in content.get("slots", {}):
            for el in els:
                fill_slot_value(el, content["slots"][name], report, name,
                                nested_map.get(name, frozenset()))
        else:
            # Same safety rule as synthetic slots and handoffs: template
            # worked-example prose never survives into a rendered document.
            # Blank the element, then report (defense in depth for non-strict
            # runs; --strict fails the render on this either way).
            for el in els:
                set_text(el, "")
            report["missing"].append(name)

    for rname, info in schema.get("repeats", {}).items():
        container = soup.find(attrs={"data-repeat": rname})
        if container is None:
            continue
        if info.get("optional_block") and rname not in content.get("repeats", {}):
            continue  # handled by the optional pass
        data = content.get("repeats", {}).get(rname)
        kind = info.get("kind", "rows")
        if kind == "grid":
            if not data or not data.get("rows"):
                remove_repeat_block(container, report, rname)
            else:
                render_grid(container, data, info, report, rname)
        elif kind == "points":
            if not data:
                remove_repeat_block(container, report, rname)
            else:
                render_points(container, data, info, report, rname)
        else:
            if not data:
                remove_repeat_block(container, report, rname)
            else:
                render_rows(container, data, info, report, rname, nested_map)

    sb = content.get("standalone_bars", [])
    standalone = [e for e in soup.find_all(attrs={"data-bar": True})
                  if not in_repeat(e) and not in_optional(e)]
    for i, el in enumerate(standalone):
        if i < len(sb):
            apply_bar(el, sb[i], report)
        elif schema.get("standalone_bars"):
            report["missing"].append(f"standalone_bars[{i}]")

    opts = soup.find_all(attrs={"data-optional": True})
    given = content.get("optionals", {})
    oschemas = {o["id"]: o for o in schema.get("optionals", [])}
    for i, el in enumerate(opts, 1):
        oid = f"optional_{i}"
        odata = given.get(oid)
        is_handoff_block = oschemas.get(oid, {}).get("handoff_block")
        if not odata and is_handoff_block:
            continue  # the handoff block is filled by fill_handoff, kept by default
        if not odata:
            el.extract()
            report["deleted"].append(oid)
            continue
        for sname, sval in (odata.get("slots") or {}).items():
            targets = [el] if el.get("data-slot") == sname else []
            targets += el.find_all(attrs={"data-slot": sname})
            for t in targets:
                fill_slot_value(t, sval, report, f"{oid}.{sname}",
                                nested_map.get(sname, frozenset()))
        for rname, rdata in (odata.get("repeats") or {}).items():
            cont = el.find(attrs={"data-repeat": rname})
            if cont is not None:
                render_rows(cont, rdata, {}, report, f"{oid}.{rname}", nested_map)

    apply_toggles(soup, content.get("toggles") or {}, report)
    fill_handoff(soup, content, content.get("artifact", ""), report)

    root = soup.find(attrs={"data-mode": True})
    if root is not None:
        if mode or content.get("mode"):
            root["data-mode"] = mode or content["mode"]
        overrides = dict(content.get("brand") or {})
        if brand:
            overrides.update(brand)
        for k, v in overrides.items():
            style_set(root, k, v)

    if ds_dir:
        inline_ds(soup, ds_dir, report)

    return soup, report


# ---------------------------------------------------------------- extract


def extract_rows(container, base_layout, base_barpaths, info=None):
    base = kids(container)[0] if kids(container) else None
    rows = []
    for row_el in kids(container):
        row = {}
        own_layout = row_slot_layout(row_el)
        if row_el is base or own_layout:
            layout, barpaths, positional = own_layout, row_bar_paths(row_el), False
        else:
            layout, barpaths, positional = base_layout, base_barpaths, True
        for sname, path in layout.items():
            try:
                el = at_path(row_el, path)
            except (IndexError, TypeError):
                # Irregular slotless row: the slotted wrapper was replaced by a
                # bare text node. Fall back to the parent's own direct text.
                if positional and path:
                    try:
                        parent = at_path(row_el, path[:-1])
                        t = direct_text(parent)
                        if t:
                            row[sname] = t
                    except (IndexError, TypeError):
                        pass
                continue
            row[sname] = slot_value_of(el, sname)
        for sname, spath in match_synthetic(info, layout).items():
            try:
                el = at_path(row_el, tuple(spath))
            except (IndexError, TypeError):
                continue
            row[sname] = direct_text(el)
        if barpaths:
            vals = []
            for path in barpaths:
                try:
                    vals.append(read_bar(at_path(row_el, path)))
                except (IndexError, TypeError):
                    vals.append(None)
            if len(vals) == 1:
                row["bar"] = vals[0]
            else:
                row["bars"] = vals
        for ncont in row_el.find_all(attrs={"data-repeat": True}):
            if ncont.find_parent(attrs={"data-repeat": True}) is not container:
                continue
            nks = kids(ncont)
            if not nks:
                continue  # empty nested container: same as absent
            row[ncont["data-repeat"]] = extract_rows(
                ncont, row_slot_layout(nks[0]), row_bar_paths(nks[0]))
        rows.append(row)
    return rows


def extract(doc_path, schema):
    soup = parse_doc(doc_path)
    content = {"template": schema.get("template"), "slots": {}, "repeats": {},
               "standalone_bars": [], "optionals": {}, "toggles": {}}
    for name, entry in schema.get("slots", {}).items():
        if entry.get("synthetic"):
            try:
                el = at_path(soup, tuple(entry["path"]))
            except (IndexError, TypeError):
                continue
            content["slots"][name] = direct_text(el)
            continue
        el = next((e for e in soup.find_all(attrs={"data-slot": name})
                   if not in_repeat(e) and not in_optional(e)), None)
        if el is None:
            continue
        ekids = kids(el)
        if entry.get("html") or len(ekids) > 1:
            content["slots"][name] = {"html": "".join(str(k) for k in ekids)}
        elif entry.get("type") == "pill" or name.endswith(".pill"):
            content["slots"][name] = parse_pill_text(clean_text(el)) or clean_text(el)
        else:
            content["slots"][name] = clean_text(el)
    for rname, info in schema.get("repeats", {}).items():
        container = soup.find(attrs={"data-repeat": rname})
        if container is None:
            continue
        kind = info.get("kind", "rows")
        ks = kids(container)
        if kind == "grid":
            n = info["data_cols"]
            cols = [clean_text(k) for k in ks[1:1 + n]]
            rows = []
            body = ks[1 + n:]
            for i in range(0, len(body), 1 + n):
                chunk = body[i:i + 1 + n]
                if len(chunk) < 1 + n:
                    break
                cells = []
                for c in chunk[1:]:
                    bg = style_get(c, "background") or ""
                    if "outline" in (c.get("style") or ""):
                        cells.append("gap")
                    else:
                        cells.append(HEAT_REVERSE.get(bg.strip(), "none"))
                rows.append({"label": clean_text(chunk[0]), "cells": cells})
            content["repeats"][rname] = {"columns": cols, "rows": rows}
        elif kind == "points":
            rows = []
            for p in ks:
                left = style_get(p, "left") or "0%"
                top = style_get(p, "top") or "0%"
                dot = next((s for s in p.find_all("span")
                            if style_get(s, "border-radius")), None)
                row = {"label": clean_text(p),
                       "x": round(float(left.rstrip("%")) / 100, 4),
                       "y": round(float(top.rstrip("%")) / 100, 4)}
                if dot is not None:
                    w = style_get(dot, "width") or ""
                    if w.endswith("px"):
                        row["size"] = int(float(w[:-2]))
                    if "--bh-accent" in (style_get(dot, "background") or ""):
                        row["accent"] = True
                rows.append(row)
            content["repeats"][rname] = rows
        else:
            if not ks:
                content["repeats"][rname] = []
                continue
            content["repeats"][rname] = extract_rows(
                container, row_slot_layout(ks[0]), row_bar_paths(ks[0]), info)
    standalone = [e for e in soup.find_all(attrs={"data-bar": True})
                  if not in_repeat(e) and not in_optional(e)]
    content["standalone_bars"] = [read_bar(e) for e in standalone]
    for i, el in enumerate(soup.find_all(attrs={"data-optional": True}), 1):
        oslots = {}
        candidates = ([el] if el.has_attr("data-slot") else []) + \
            el.find_all(attrs={"data-slot": True})
        for s in candidates:
            if s["data-slot"].startswith("handoff."):
                continue  # captured flat under content["handoff"]
            oslots[s["data-slot"]] = clean_text(s)
        if oslots:
            content["optionals"][f"optional_{i}"] = {"slots": oslots}
    m = re.search(r"state\s*=\s*\{([^}]*)\}", str(soup))
    if m:
        for name, val in re.findall(r"(\w+)\s*:\s*(true|false)", m.group(1)):
            content["toggles"][name] = val == "true"
    hs = {}
    for el in soup.find_all(attrs={"data-slot": True}):
        if el["data-slot"].startswith("handoff."):
            hs[el["data-slot"].split(".", 1)[1]] = clean_text(el)
    if hs:
        content["handoff"] = hs
    return content


# ---------------------------------------------------------------- verify


def verify(doc_path, template_path, schema, content_path=None):
    doc = parse_doc(doc_path)
    tpl = parse_doc(template_path)
    findings = []

    def add(sev, check, evidence):
        findings.append({"severity": sev, "check": check, "evidence": evidence})

    # Scan rendered text only: the inlined design-system CSS/JS carries its own
    # comments and is not artifact prose.
    prose_doc = BeautifulSoup(str(doc), "html.parser")
    for t in prose_doc.find_all(["style", "script"]):
        t.extract()
    for el in prose_doc.find_all(string=lambda s: EM_DASH in s):
        add("HIGH", "em-dash", str(el).strip()[:90])
    # The banned-list exhibit (TK_05's data-repeat="banned") displays the
    # forbidden phrases ON PURPOSE; exclude it from the phrase scan so the
    # exhibit does not flag itself. Everywhere else the scan stays strict.
    # Template-anchored: honored only when the TEMPLATE itself ships a banned
    # exhibit, so a wrapper smuggled into another artifact's doc buys nothing.
    if tpl.find(attrs={"data-repeat": "banned"}) is not None:
        for t in prose_doc.find_all(attrs={"data-repeat": "banned"}):
            t.extract()
    # Guidance/annotation elements marked data-verify-exempt quote banned
    # phrases ON PURPOSE (e.g. TK_05's "Never" callout, note.body slot) to
    # tell the recruiter what NOT to write; exclude them from the phrase scan
    # only -- em-dash and every other check below still sees them in full.
    # Template-anchored (F1): the exemption is honored only for slots the
    # TEMPLATE marks data-verify-exempt. set_html() already strips control
    # attributes from content-supplied fragments at render time; this anchor
    # protects verify independently, for documents from any other source.
    # Candidate-facing copy slots (email bodies, subjects, inmails) never
    # carry the marker in any template, so they stay scanned at full strength.
    tpl_exempt = {t.get("data-slot")
                  for t in tpl.find_all(attrs={"data-verify-exempt": True})}
    tpl_exempt.discard(None)
    for t in prose_doc.find_all(attrs={"data-verify-exempt": True}):
        if t.get("data-slot") in tpl_exempt:
            t.extract()
    body_text = prose_doc.get_text(" ").lower()
    for p in FORBIDDEN_PHRASES:
        if p in body_text:
            add("HIGH", "forbidden-phrase", p)

    for el in doc.find_all(attrs={"data-bar": True}):
        raw_bar = (el.get("data-bar") or "").strip()
        style = el.get("style") or ""
        try:
            if "," in raw_bar:
                a, b = [float(x) for x in raw_bar.split(",")]
                left = style_get(el, "left") or "0%"
                width = style_get(el, "width") or "0%"
                lv = float(left.rstrip("%")) if left != "0" else 0.0
                wv = float(width.rstrip("%"))
                if abs(lv - a * 100) > 0.5 or abs((lv + wv) - b * 100) > 0.5:
                    add("HIGH", "data-bar geometry",
                        f"range {raw_bar} vs left:{left};width:{width}")
            elif "conic-gradient" in style:
                v = float(raw_bar)
                # Parse stops from the conic-gradient() segment only: the full
                # style string carries unrelated percentages (border-radius:50%).
                gm = re.search(r"conic-gradient\(([^)]*)\)", style)
                stops = re.findall(r"([\d.]+)%", gm.group(1)) if gm else []
                if stops and abs(float(stops[0]) - v * 100) > 0.5:
                    add("HIGH", "data-bar geometry",
                        f"donut {raw_bar} vs first stop {stops[0]}%")
            elif style_get(el, "min-height") and not clean_text(el):
                v = float(raw_bar)  # heat cell: background encodes, spot check vocab
                if fmt_bar(v) not in {s["bar"] for s in HEAT_STRENGTH.values() if s["bar"]}:
                    add("MEDIUM", "heat-cell value", raw_bar)
            else:
                v = float(raw_bar)
                width = style_get(el, "width")
                if width and width.endswith("%") and abs(float(width[:-1]) - v * 100) > 0.5:
                    add("HIGH", "data-bar geometry", f"{raw_bar} vs width:{width}")
        except (ValueError, TypeError):
            add("MEDIUM", "data-bar parse", raw_bar)

    # Example survival, two tiers. The worked example is a Propulsion Engineer
    # search at Onepromptman: its DOMAIN language surviving in another search is
    # a certain failure (qa-gate check 3a). A slot merely identical to the
    # example may be legitimate structural text (an artifact eyebrow, a metric
    # name, an A/B frame label), so it goes to the review queue as MEDIUM, not
    # HIGH. handoff.* slots are derived constants and are skipped. DOMAIN_MARKERS
    # / SANCTIONED_CREDIT live at module scope (near MIN_SYNTHETIC_LEN) so
    # lint_template() shares this exact scan instead of a second copy of it.
    for el in doc.find_all(True):
        t = clean_text(el)
        if t and SANCTIONED_CREDIT in t.lower():
            continue
        if t and DOMAIN_MARKERS.search(t) and len(t) < 400:
            slot = el.get("data-slot", el.name)
            add("HIGH", "surviving example text",
                f"{slot}: worked-example domain language: {t[:70]}")
            break  # one finding is enough; qa-gate cites exact slots
    # tpl_texts is built WITHOUT a length floor (round-2 fix, M6) so the new
    # short-risky check below can reuse the exact same object; the >= 25
    # check right after it is unchanged -- it still applies its own floor at
    # the point of use, so a text under 25 chars was never going to satisfy
    # it anyway and this broadening is a no-op for that check's results.
    tpl_texts = {}
    for el in tpl.find_all(attrs={"data-slot": True}):
        t = clean_text(el)
        if t:
            tpl_texts.setdefault(el["data-slot"], set()).add(t)
    for el in doc.find_all(attrs={"data-slot": True}):
        name = el["data-slot"]
        if name.startswith("handoff."):
            continue
        t = clean_text(el)
        if len(t) >= 25 and t in tpl_texts.get(name, ()):
            add("MEDIUM", "identical to example (review)", f"{name}: {t[:70]}")
        # M6 (round-2, second red-team): the >= 25 floor above is a real gap
        # for SHORT slot content -- a rendered slot whose text is IDENTICAL
        # to the template's own example for that slot AND looks like risky
        # comp/date/domain data (e.g. a bare "105k") ships silently on a
        # non-strict render when an agent omits the key, with nothing above
        # catching it (the >= 25 check floors right past it). Scoped to
        # < 25 chars specifically -- it closes the gap the existing check
        # leaves, rather than duplicating a second finding for text the
        # existing check already flags.
        elif t and len(t) < 25 and t in tpl_texts.get(name, ()) and RISKY_TEXT_PATTERN.search(t):
            add("HIGH", "identical to example (risky)", f"{name}: {t[:70]}")

    for el in doc.find_all(attrs={"data-repeat": True}):
        ks = kids(el)
        if not ks:
            add("HIGH", "empty repeat", el["data-repeat"])
            continue
        band = (el.get("data-count") or "").strip()
        m = re.match(r"(\d+)\s*-\s*(\d+)$", band)
        if m and el.get("data-repeat") in schema.get("repeats", {}) and \
                schema["repeats"][el["data-repeat"]].get("kind", "rows") == "rows":
            lo, hi = int(m.group(1)), int(m.group(2))
            if not (lo <= len(ks) <= hi):
                add("MEDIUM", "data-count band",
                    f"{el['data-repeat']}: {len(ks)} rows, band {band}")

    for el in doc.find_all(attrs={"data-slot": True}):
        if el["data-slot"].endswith(".pill"):
            t = clean_text(el)
            if t not in PILL_STYLES and not parse_pill_text(t):
                add("HIGH", "pill vocabulary", f"{el['data-slot']}: {t!r}")
    for bad in ("TBD", "N/A", "Data not available", "NOT_FOUND", "[Insert", "TODO"):
        if bad.lower() in body_text:
            add("HIGH", "placeholder text", bad)

    if content_path:
        content = json.loads(read(content_path))
        for frag_name, val in (content.get("slots") or {}).items():
            if isinstance(val, dict) and "html" in val and "style=" in val["html"]:
                add("MEDIUM", "html fragment carries style attr", frag_name)

    # Template-furniture lint (lint_template()): the BOUND TEMPLATE's own
    # verbatim-copy surface, independent of what this particular render
    # filled in -- a template that still exposes risky unslotted furniture
    # is a standing risk for every future render off it, not just this doc.
    # Attribute-borne findings are an informational tier (SHOULD-FIX, not a
    # MUST-FIX silent-miss class): MEDIUM, not HIGH. Every other surface
    # escalates to HIGH as before. The evidence string spells out that this
    # is a TEMPLATE defect, not a content problem -- a content patch cannot
    # clear this finding on the next render, only editing the bound
    # template can; without that pointer the documented remediation path
    # (route findings back to the owning agent as a content patch) loops
    # forever on a finding no content patch can fix.
    for w in lint_template(template_path):
        sev = "MEDIUM" if w.get("surface") == "attribute" else "HIGH"
        add(sev, "template furniture",
            _format_lint_finding(w) +
            " [TEMPLATE defect: fix the bound template (add data-slot or "
            "remove the text) -- a content patch cannot clear this finding, "
            "it will recur on every future render off this template]")

    return findings


# ---------------------------------------------------------------- pack validation


def _walk_pv(node, path, findings):
    if isinstance(node, dict):
        if "pill" in node:
            if node["pill"] not in PILL_STYLES:
                findings.append({"severity": "HIGH", "check": "pill vocabulary",
                                 "evidence": f"{path}: {node['pill']!r}"})
            if not str(node.get("method", "")).strip():
                findings.append({"severity": "HIGH", "check": "pv missing method",
                                 "evidence": path})
            if node["pill"] == "Sourced" and not re.search(
                    r"\b(19|20)\d{2}\b", str(node.get("method", "")) + str(node.get("as_of", ""))):
                findings.append({"severity": "MEDIUM", "check": "Sourced without vintage",
                                 "evidence": path})
        for k, v in node.items():
            _walk_pv(v, f"{path}.{k}", findings)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_pv(v, f"{path}[{i}]", findings)
    elif isinstance(node, str):
        if EM_DASH in node:
            findings.append({"severity": "HIGH", "check": "em-dash",
                             "evidence": f"{path}: {node[:60]}"})
        if node.strip() in ("TBD", "N/A", "NOT_FOUND"):
            findings.append({"severity": "HIGH", "check": "placeholder",
                             "evidence": path})


def validate_pack(pack_path, research_path=None):
    findings = []
    pack = json.loads(read(pack_path))
    for req in ("role", "built"):
        if req not in pack:
            findings.append({"severity": "HIGH", "check": "missing key", "evidence": req})
    role = pack.get("role", {})
    for req in ("title", "level", "company"):
        if not role.get(req):
            findings.append({"severity": "HIGH", "check": "missing key",
                             "evidence": f"role.{req}"})
    if pack.get("pack_version") != "1.0":
        findings.append({"severity": "MEDIUM", "check": "pack_version",
                         "evidence": str(pack.get("pack_version"))})
    if "constraints" in pack and not isinstance(pack["constraints"], list):
        findings.append({"severity": "HIGH", "check": "constraints must be a list",
                         "evidence": type(pack["constraints"]).__name__})
    # Web-budget audit (enforcement-by-audit: scout is a prompt, nothing
    # executes between its tool calls, so the budget is enforced here from
    # scout's self-reported spend, not by an interpreter).
    calls = pack.get("web_calls_used")
    if calls is not None and not isinstance(calls, int):
        findings.append({"severity": "HIGH", "check": "web_calls_used must be an integer",
                         "evidence": type(calls).__name__})
    elif isinstance(calls, int) and calls > 12:
        findings.append({"severity": "HIGH", "check": "web budget exceeded",
                         "evidence": f"web_calls_used {calls} > 12"})
    elif calls is None and "scout" in (pack.get("built_from") or []):
        findings.append({"severity": "MEDIUM", "check": "web_calls_used missing",
                         "evidence": "scout-built pack reports no web-call count"})
    _walk_pv(pack, "pack", findings)
    if research_path:
        research = json.loads(read(research_path))
        _walk_pv(research, "research", findings)
        for p in research.get("quadrant", []):
            for ax in ("x", "y"):
                if not (0 <= float(p.get(ax, -1)) <= 1):
                    findings.append({"severity": "HIGH", "check": "quadrant range",
                                     "evidence": f"{p.get('name')}: {ax}"})
    return findings


# ---------------------------------------------------------------- compat handoffs


def append_compat_handoff(handoffs_path, content, role, schema=None):
    p = Path(handoffs_path)
    data = {}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    art = content.get("artifact", "")
    if not art and schema:
        # Content files routinely omit the envelope metadata; the bound
        # template's TK_NN number is authoritative (1.0.1 live-run fix:
        # entries were collapsing onto an empty-string key).
        m = re.search(r"TK_(\d{2})", schema.get("template", ""))
        if m:
            art = m.group(1)
    h = content.get("handoff") or {}
    entry = {"artifact": art, "agent": AGENT_BY_ARTIFACT.get(art, ""),
             "role": role or "", "generated": content.get("generated", ""),
             "derived_from": "content-render 1.0",
             "handoff": h.get("keys") or {}}
    if h.get("assumptions"):
        entry["handoff"]["assumptions"] = h["assumptions"]
    data[art] = entry
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- main


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schema")
    s.add_argument("--template", required=True)
    s.add_argument("--slot-types")
    s.add_argument("--out")

    e = sub.add_parser("extract")
    e.add_argument("--template")
    e.add_argument("--schema", required=True)
    e.add_argument("--doc", required=True)
    e.add_argument("--out")

    r = sub.add_parser("render")
    r.add_argument("--template", required=True)
    r.add_argument("--schema", required=True)
    r.add_argument("--content", required=True)
    r.add_argument("--ds")
    r.add_argument("--out", required=True)
    r.add_argument("--mode")
    r.add_argument("--brand", nargs="*", default=[])
    r.add_argument("--handoffs")
    r.add_argument("--role")
    r.add_argument("--strict", action="store_true",
                   help="exit 1 when required slots are missing")

    v = sub.add_parser("verify")
    v.add_argument("--template", required=True)
    v.add_argument("--schema", required=True)
    v.add_argument("--doc", required=True)
    v.add_argument("--content")
    v.add_argument("--out")

    lt = sub.add_parser("lint-template")
    lt.add_argument("--template", required=True)
    lt.add_argument("--out")

    p = sub.add_parser("validate-pack")
    p.add_argument("--pack", required=True)
    p.add_argument("--research")
    p.add_argument("--out")

    args = ap.parse_args(argv)

    def emit(obj, out):
        text = json.dumps(obj, indent=1, ensure_ascii=False)
        if out:
            Path(out).write_text(text, encoding="utf-8")
            print(out)
        else:
            print(text)

    if args.cmd == "schema":
        schema = build_schema(args.template, args.slot_types)
        furniture = lint_template(args.template)
        if furniture:
            schema["furniture_warnings"] = furniture
            for w in furniture:
                sys.stderr.write(f"WARNING: template furniture: {_format_lint_finding(w)}\n")
        emit(schema, args.out)
    elif args.cmd == "extract":
        schema = json.loads(read(args.schema))
        emit(extract(args.doc, schema), args.out)
    elif args.cmd == "render":
        schema = json.loads(read(args.schema))
        content = json.loads(read(args.content))
        brand = {}
        for kv in args.brand:
            k, _, v2 = kv.partition("=")
            brand[k] = v2
        soup, report = render(args.template, schema, content,
                              ds_dir=args.ds, mode=args.mode, brand=brand)
        failed = bool(report["errors"] or (args.strict and report["missing"]))
        # Atomic write: render to a temp file next to --out and only move it
        # into place when the render is clean. Writing straight to --out on a
        # failed render is an exit-code trap -- a caller that just checks
        # "does the output file exist" sees one and calls it done, while the
        # real signal (report["errors"], the exit code) says otherwise, and
        # any prior good artifact at --out would get clobbered by the broken
        # one. On failure the attempt is kept under a .failed suffix for
        # inspection, never at the canonical --out path.
        out_path = Path(args.out)
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        tmp_path.write_text(str(soup), encoding="utf-8")
        if failed:
            failed_path = out_path.with_name(out_path.name + ".failed")
            tmp_path.replace(failed_path)
            summary = {"out": None, "attempted_out": args.out,
                       "failed_artifact": str(failed_path),
                       **{k: v for k, v in report.items() if v}}
            print(json.dumps(summary, indent=1, ensure_ascii=False))
            sys.exit(1)
        tmp_path.replace(out_path)
        if args.handoffs:
            append_compat_handoff(args.handoffs, content, args.role, schema)
        summary = {"out": args.out, **{k: v for k, v in report.items() if v}}
        print(json.dumps(summary, indent=1, ensure_ascii=False))
    elif args.cmd == "verify":
        schema = json.loads(read(args.schema))
        findings = verify(args.doc, args.template, schema, args.content)
        emit({"doc": args.doc, "findings": findings,
              "verdict": "PASS" if not [f for f in findings
                                        if f["severity"] == "HIGH"] else "FAIL"},
             args.out)
        sys.exit(0 if not [f for f in findings if f["severity"] == "HIGH"] else 1)
    elif args.cmd == "lint-template":
        findings = lint_template(args.template)
        emit({"template": args.template, "findings": findings,
              "verdict": "CLEAN" if not findings else "FLAGGED"}, args.out)
        sys.exit(0 if not findings else 1)
    elif args.cmd == "validate-pack":
        findings = validate_pack(args.pack, args.research)
        emit({"pack": args.pack, "findings": findings,
              "verdict": "PASS" if not [f for f in findings
                                        if f["severity"] == "HIGH"] else "FAIL"},
             args.out)
        sys.exit(0 if not [f for f in findings if f["severity"] == "HIGH"] else 1)


if __name__ == "__main__":
    main()
