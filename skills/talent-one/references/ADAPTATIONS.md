# Cowork adaptations (authoritative deltas)

This kit was originally architected for n8n / Claude Projects. The reference files 00_SHARED_CORE.md and 02_GROUNDING_MATRIX.md remain authoritative for agent behavior, with these deltas. Where an original file conflicts with this list, this list wins.

1. **No config.yaml.** The configuration surface is `talent-one-profile.md`, written by the talent-one-setup skill and passed to agents inside their prompts. `{organization.*}`, `config.constraints[]`, `config.branding`, and `config.resources` all resolve from the profile.
2. **No out/ directory. Folders are per role; runs sit inside them.** The role home is
    `talent-one-roles/<role_slug>/` in the user's working folder. It holds `inputs/`
    (material the user supplies: an existing JD, an intake doc, a comp export, a prior
    posting), `ROLE.md` (one line per run: date, artifacts built, QA verdict, seeded
    keys; written by the skill, never read by agents), and `runs/<YYYY-MM-DD>/`. A run
    folder's contract is unchanged: artifacts, `handoffs.json`, `QA_REPORT.md`. Agents
    receive one run folder path and know nothing about the layout above it; qa-gate
    still audits exactly one run folder. `<role_slug>` carries the client company when
    the profile covers more than one (`<company>-<role>`), so the same title for two
    clients never collides. Legacy `talent-one-runs/<date>_<role_slug>/` folders stay
    readable and are never moved, renamed, or rewritten; new runs write to the new
    layout only. Relay globs both `talent-one-roles/*/runs/*/handoffs.json` and the
    legacy `talent-one-runs/*/handoffs.json`, reads the `role` field inside the file,
    and falls back to the folder slug when that field is absent. The relay agent owns
    cross-run reuse and the freshness table (default 90/135 days; Atlas 60; comp SLA
    6 months).
3. **No scripts.** `check_dag.py`, `check_fill.py`, and the benchmark extractor do not exist here. The DAG is enforced by the relay agent's fixed table; fill integrity and provenance are enforced by the qa-gate agent; a benchmark file is optional at `<run folder>/kb/benchmarks/` and its absence routes agents to their public fallback sources.
4. **Templates ship FILLED** with a worked example (a Propulsion Engineer search at Onepromptman). Agents replace content in place per 00_SHARED_CORE.md §5, which is authoritative. Any statement elsewhere that templates are "blank" is wrong.
5. **Honesty vocabulary is the three pills only** (Sourced / Estimate / Internal) per 00_SHARED_CORE.md §3. "NOT_FOUND", "TBD", "N/A", and hedging placeholders are QA failures; the honest empty state is deleting the block.
6. **Repair loops: maximum 2**, enforced by the orchestrator skill.
7. **Internal systems are optional.** ATS / wiki / comp-system / brand-doc reads happen only through connected MCP tools (see CONNECTORS.md at plugin root). The standalone public-data path (02_GROUNDING_MATRIX.md Part 1.5) is the default and is fully supported. The KB `MIRROR.md` and gitignore workflow do not apply.
8. **Self-contained output.** Every artifact inlines the `_ds` design system (tokens.css then styles.css in one `<style>` block, `_ds_bundle.js` inlined) so files render standalone anywhere.
9. **Source codenames stay internal.** In artifact-facing citation text, use plain source names ("BLS OES 2024", "DOL disclosure data 2025", "levels.fyi 2026"), not internal codenames like OFLC/GEM-BM/LTI.
10. **hm_names / recruiter_names** are per-run inputs and may print in artifacts. No name ever enters a web query; candidate names never appear anywhere.
11. **handoff.produces rendering.** The grounding matrix's handoff-key tables use `[]` to mark list-typed keys. That notation is documentation only: when rendering `handoff.produces` in an artifact, list the bare key names exactly as they appear in your HANDOFF_JSON (no `[]` suffixes). In tables, a non-applicable cell is `-`, never "n/a". Pill labels are exactly Sourced, Estimate, or Internal (never "Modeled").
12. **Preflight and NEED_INPUT are mandatory.** Every agent runs the preflight in
    00_SHARED_CORE.md §1.5 before any research, and halts with a NEED_INPUT block
    (§6.5) when a named input is missing. Missing named input equals halt. Failed
    lookup equals degrade honestly. Subagents have no AskUserQuestion tool: the
    orchestrator is the only channel to the user and batches every `ask_user` item
    into a single pass. Relay preflights the whole plan before anything expensive
    runs; per-agent preflight is the backstop for direct invocation.
    **This supersedes any agent prompt instructing you to record a missing required
    value in `handoff.blocked` and continue.** That instruction applies to values
    genuinely unavailable in the world, never to inputs the orchestrator named but did
    not deliver.
13. **Seeded handoffs.** A `handoffs.json` entry may be written by a skill from material
    the user supplies in `inputs/`, or from the user's own stated answer, instead of by
    running its producer agent. This is the supported way to run an agent without its
    upstream chain. It does not relax §1.5: a seed satisfies an input, it never excuses
    a missing one.
    a. A seed uses the producer's exact keys from `02_GROUNDING_MATRIX.md` Part 3.5. No
       new key names, no renames, same token budget.
    b. A seed fills only the keys its source actually states. Any unstated key is
       OMITTED. Omitted equals absent: the consumer's preflight still halts on it
       (Class A). Never write a placeholder to silence a halt.
    c. Shape, keyed by artifact number like any other entry:
       `{"artifact":"02","agent":"JD-BOT","role":"<slug>","generated":"<YYYY-MM-DD>",
       "seed":true,"seeded_from":"inputs/<file>|user_stated","seeded_on":"<YYYY-MM-DD>",
       "caveat":"<one line naming what this seed does not establish>",
       "handoff":{ ...only the keys the source states... }}`
       `generated` keeps relay's freshness logic working; it is the date the entry was
       written.
    d. Provenance floor. A value read from a dated, named document is Sourced, cited by
       document name and date. A value the user asserted is an Estimate with
       "recruiter-stated" as its method. Nothing from a seed is Internal unless the
       material is an export from the client's own system of record. A seed never
       upgrades a pill.
    e. The consumer copies the seed's `caveat` verbatim into its `handoff.assumptions`
       (see the Part 3.5 note on that key), and into a Caution callout where the seed
       drives visible content.
    f. Atlas stays the sole source of market classification. `market`, `funnel`,
       `comp_guidance`, and `personas[]` seed only from a dated market document or a
       cached Atlas run, never from an assertion. No such source means run Atlas or
       drop the artifact.
    g. `constraints[]` is never seeded. Eligibility text comes from the profile only,
       verbatim, per 00_SHARED_CORE.md §4 and qa-gate check 4a.
    h. Skills write seeds; agents never do. Only skills hold a user channel. Relay
       names seed candidates in its plan; the orchestrating skill reads the source,
       confirms with the user, and writes the entry before the spawn, under its own
       input-preflight rule. This is input capture, not artifact authoring.
    i. A provided JD seeds A02's keys and, where the document states them, A07's
       `requirements[]` and `comp_frame`. JD-BOT, when it runs, treats the supplied JD
       as the intake draft its calibration ledger diffs against, never as a finished
       artifact. If the user wants no JD artifact this run, the seeded A02 entry alone
       lets A04 HUNTER run.
14. **The JD can ship as a plain document.** When the orchestrator's prompt sets
    `plain_doc` (values: `markdown`, `docx`, `both`), JD-BOT also writes the posting
    body beside its HTML artifact, same stem, `.md` extension, whichever value is set.
    Markdown is authored by JD-BOT. docx conversion is the skill's job, never the
    agent's, and is a conversion of that markdown file, never a retyping. The two
    representations carry the same posting prose word for word. Provenance pills, the
    annotation rail, and the calibration ledger stay in the HTML: the posting is a
    document a candidate reads, not an audited artifact. A disqualifying constraint
    renders verbatim in both. The branded HTML stays the default, is always written,
    and is the only representation qa-gate audits for fill integrity; `plain_doc` is
    strictly opt-in.
15. **A role spec is the minimum input; a JD is not a gate.** Every chain needs a role
    spec: either material in `inputs/` (a JD, an intake doc, a comp export) or the
    answers to relay's ask-first list. No artifact is a prerequisite for another beyond
    the DAG in `relay.md`. A user-supplied JD is a seed (item 13i), not a gate: it
    shortens the work, it does not replace A03's market read, and it never blocks
    running the real agents instead.
16. **Intake always solicits a brain dump.** Every skill that starts a run offers,
    once, in one plain message before spawning relay: paste or attach anything you
    already have (a JD, intake notes, comp data, links, or a straight brain dump), or
    say skip. Chip questions (AskUserQuestion) carry scalar facts only; free context
    always gets the open invitation, because four chips cannot carry a brain dump.
    Filing: company-level material captured during setup goes under `talent-one-kb/`
    by KB category (`brand/`, `benchmarks/`, `internal/`, `history/`) and the profile
    records `kb_root: talent-one-kb/` in resources; role-level material goes under
    `talent-one-roles/<role_slug>/inputs/`. Pasted text becomes a dated
    `braindump-<YYYY-MM-DD>.md`, verbatim, never reformatted. The offer never blocks:
    skip means public-data defaults, a supported path, not a degraded one. Never ask
    twice in one run.

---

## Talent One 1.0: the content/render split (items 17-31 override any earlier item they touch)

17. **The Context Pack replaces handoffs as the runtime data path.** One research
    pass per role (the `scout` agent, or seeding/import) writes
    `talent-one-roles/<role_slug>/pack.json` + `pack-research.json` per
    `CONTEXT_PACK.md`, and every artifact agent runs against the pack, all in
    parallel. The 0.9.x sequential DAG (calibrate then sensei then atlas then the
    rest) no longer exists; relay plans pack state and parallel phase 2 instead of
    dependency chains. Item 13's seeding rules survive with the pack as the
    destination; Part 3.5 keys survive as audit vocabulary and migration mapping
    (`CONTEXT_PACK.md` §7). handoffs.json in a 1.0 run folder is derived by the
    renderer for compatibility and audit, never read at runtime, never hand-edited.
18. **Agents emit content JSON; a script renders HTML.** Shared core §5 (v2.0) is
    the contract: agents write `<run folder>/content/<NN>.content.json` against
    `references/content-schemas/TK_<NN>.content-schema.json` (worked example
    beside it) and never open templates. `scripts/render.py` fills the template,
    syncs every data-bar geometry form, styles pills, deletes empty blocks, inlines
    the design system, applies branding, derives the rendered handoff block, and
    writes the compat handoffs.json. This supersedes item 3's "no scripts": the
    renderer, its `verify`, and `validate-pack` ship in the plugin and are
    mandatory pipeline steps. Item 8 (self-contained output) is now enforced by the
    renderer rather than by agents.
19. **qa-gate audits content, not HTML.** Inputs: pack, content JSONs, compat
    handoffs, and `render.py verify` reports (geometry, surviving example text, em
    dashes, forbidden phrases, placeholders, pill vocabulary are machine findings).
    Rendering is deterministic, so certifying the content certifies the artifact.
    Repairs are content patches routed to the owning agent, then a free re-render;
    the 2-loop maximum (item 6) is unchanged.
20. **Update mode.** The role home caches each artifact's latest accepted content
    JSON in `talent-one-roles/<role_slug>/content/`. An update = change the pack
    (with provenance) where the fact changed, regenerate only affected fields via
    the owning agent (or a direct orchestrator patch for pure 1:1 presentational
    edits), re-render, re-verify. Rendered HTML is never edited.
21. **Freshness is per pack section** (`CONTEXT_PACK.md` §4): market/targets 60
    days, comp 6 months hard, everything else 90/135. Relay applies the table to
    section stamps; a sectional scout run refreshes only what is stale. This
    replaces the per-artifact freshness rows for pack-carried data; artifact
    regeneration follows the pack.
22. **External pack building.** `references/PACK_RESEARCH_PROMPT.md` is a
    paste-ready deep-research prompt whose output conforms to the pack schema. The
    skill validates (`render.py validate-pack`), installs it as the pack with
    provenance intact, and marks `built_from: external-deep-research`. A validated
    external research file with named dated sources satisfies item 13f's bar for
    market/funnel/comp/personas; a bare assertion still never does.
23. **Model tiers per agent** (frontmatter `model:`): relay, jdbot, and
    recruiter-screen run haiku (pack-fed, tightly contracted, no research duties);
    scout and the remaining artifact agents run sonnet (bounded research +
    judgment); qa-gate runs opus (small input, final judgment gate). Aliases, not
    pinned versions, so installs track current models.
24. **NEED_INPUT vocabulary updated** (shared core §6.5): `kind` gains `pack_key`,
    `cheapest_fix` values are `ask_user | orchestrator_writes_file | run_scout`
    (replacing `run_upstream_agent`). Item 12 otherwise unchanged: halt on missing
    named inputs, degrade on empty world lookups, skills hold the only user
    channel.
25. **Synthetic prose slots (1.0.1, fix F1).** `render.py schema` emits
    `"synthetic": true` slot entries for unslotted template text of 45+
    characters (repeat base rows as `<repeat>.proseN`, row variants as
    `<repeat>.vP.proseN`, top-level as `doc.proseN`), each with the structural
    path and an example excerpt. The renderer fills them by path; a MISSING
    synthetic value renders blank and is listed in the render report, so
    worked-example prose can never survive into a client artifact. The
    positional text patch for slotless example rows is capped below 45
    characters. Shared core §5.2 now requires agents to fill schema-listed
    synthetic slots like any other slot. Extract reads them back, keeping the
    fixed-point round-trip exact on all 8 templates.
26. **Precompiled agent briefs (1.0.1, fix F2).** `scripts/build_briefs.py`
    generates `references/briefs/<agent>.md` at build time: the agent's
    shared-core sections, its grounding-matrix block, a compact schema summary
    (synthetic slots marked), and its CONTEXT_PACK §5 row. Agent RUNTIME blocks
    read the brief ONLY (scout additionally reads `baselines.json`). Briefs are
    generated artifacts: edit the sources, re-run the script (idempotent;
    `--check` verifies freshness). Roughly 60KB of per-spawn reading drops to
    about 20KB.
27. **Scout web budget and bundled baselines (1.0.1, fix F3).** Hard total
    budget of 12 web calls per full pack build (searches + fetches combined).
    `references/baselines.json` ships a vintaged snapshot (BLS OEWS occupations,
    ACS metro stats, recruiting benchmark constants); scout loads it before any
    web call and spends the budget only on role-specific facts. Baseline
    citations carry the file's own `as_of`, never today's date; a baseline entry
    pills exactly as the equivalent live lookup would, and `confidence:
    unverified` entries never become Sourced from the file alone.
28. **Market classification vocabulary unified (1.0.1, fix F4a).**
    `market.classification` is ABUNDANT | BALANCED | TIGHT | SCARCE, defined
    once in CONTEXT_PACK.md §3 with the legacy 0.9.x mapping (LOOSE, MODERATE,
    TIGHT, CRITICAL). hunter.md and jdbot.md rewritten to the pack vocabulary;
    no second scale survives anywhere.
29. **Verify checker: sanctioned credit exemption (1.0.1).** The domain-marker
    scan exempts text carrying the exact sanctioned footer credit ("Built with
    Talent One by Onepromptman"); any other use of the studio name still flags
    HIGH as wording drift.
30. **1.0.2 public-release hardening.** Six changes, each machine-verified:
    (a) rendered documents are fully self-contained: `inline_ds()` strips the
    templates' Google Fonts preconnect/stylesheet links and the
    concatenation-dead `@import` lines, so output carries zero external
    references and offline rendering falls back to the system font stacks;
    (b) the verify phrase scan excludes elements marked
    `data-verify-exempt="phrase-scan"` (slot identity, never phrase-quoting
    heuristics: only TK_05's guidance `note.body` carries the marker;
    candidate-facing copy slots stay scanned at full strength, and the
    em-dash and every other check still see exempt elements). The exemption
    cannot be smuggled: `set_html()` strips renderer control attributes
    (`data-verify-exempt`, `data-repeat`, `data-bar`, `data-count`,
    `data-optional` unconditionally; `data-slot` per the item-31 template
    anchor) from content-supplied html fragments at render time, and verify
    honors the marker, like the banned-list exclusion, only where the bound
    TEMPLATE itself carries it. Known
    residual: a hand-edited document (never a rendered one) can still fake
    the banned-list wrapper, or a forged exempt guidance slot, on the one
    template that legitimately carries them;
    hand-editing rendered HTML is already a doctrine violation, and qa-gate
    scans the raw content JSON where no such markup can hide;
    (c) `unslotted_text_paths()` treats a whole-row slot (path `()`) as
    covering every descendant path, removing the fragile redundant synthetic
    slot that made TK_01 fail on non-example content (TK_01 schema and
    example content regenerated; `extract(template) == example-content`
    held for all eight artifacts at the time of writing — superseded in
    1.0.3: items 32-35 genericize dead variant literals, so example content
    is now authored, not derivable from the template; the enforced
    invariant is `extract(render(example)) == example`, which holds 8/8);
    (d) `render.py render` writes atomically: on a failed render `--out` is
    left untouched and the attempt is kept at `<out>.failed`;
    (e) TK_05's worked-example subject debris (`[[TestRecordFact]]`, the one
    em dash in the corpus) replaced with the slot's canonical example text,
    template-first with schema and content regenerated by script;
    (f) the 12-call web budget is enforced by audit: scout self-reports
    `pack.web_calls_used`, `validate-pack` flags overage (HIGH) or a missing
    count on a scout-built pack (MEDIUM), qa-gate check 0.5 confirms the
    flag surfaces, and `build_briefs.py` fails (exit 1, `--check` included)
    on its 24KB hard ceiling instead of warning.
31. **1.0.2 final QA round (four confirmed findings + two guards, each
    reproduced before fixing and machine-verified after).**
    (a) *Nested-slot round trip restored.* Item 30(b)'s unconditional
    `data-slot` strip destroyed the one legitimate nested slot in the pack
    (TK_08 `sell.date` inside `sell.script`): the follow-up date vanished
    silently and the content-to-document-to-content round trip went 7/8.
    `data-slot` is now template-anchored per slot: a fragment filling slot S
    may keep exactly the nested slot names the bound template declares
    inside S's own element (`build_nested_slot_map`, computed from the
    pristine template before any fill); every other `data-slot` name, and
    every other control attribute, is stripped as before. Round trip is 8/8;
    the smuggle battery, including cross-slot shadowing of a sibling slot's
    name, still flags or destroys every attack.
    (b) *Every document has a single-document skill.* `talent-one-educate`
    (artifact 01, sensei) joins the seven existing ones; the orchestrator's
    description now names the educational brief consistently.
    (c) *Brief freshness is date-independent.* The generated-brief header
    carries a content-addressed source fingerprint (sha256 over the builder
    and its source files) instead of a build date, so `--check` compares
    cleanly on any day; the builder is byte-deterministic again.
    (d) *Strict rendering in every documented flow.* Every embedded render
    command carries `--strict`: a missing required or synthetic slot fails
    the render (exit 1, `.failed` artifact) instead of shipping a silently
    blanked region, and the failure routes to the owning agent as a content
    patch. Two renderer guards ride along: a JSON `null` on a synthetic slot
    blanks and reports as missing (it previously rendered the literal string
    "None" at exit 0, invisible to verify), and a missing real slot now
    blanks its element so template worked-example prose never survives a
    non-strict render either, making item 25's guarantee true for every
    slot class.

32. **TK_02 comp-band axis ticks slotted (2026-08-10).** `comp.rows`'
    BASE row shipped three axis-tick divs ('105k low end' / '135k typical' /
    '174k high end') with no `data-slot`, under item 25's 45-char synthetic
    floor. Because `render_rows`' slotless-row path clones the BASE row and
    only positionally copies unslotted text back onto matching paths (a
    no-op here: the variant "posting" row has no tick divs at that path, so
    the copy silently fails and the clone keeps whatever the BASE element
    already carries), EVERY rendered row, including the base row itself,
    showed the template's literal example numbers regardless of content —
    confirmed live: a JD shipped with 105k/135k/174k ticks against an
    approved $200-260K band. Fix: the three numeric tick texts are now
    `comp.low`/`comp.mid`/`comp.high`, each on its own inline `<span
    data-slot="...">` wrapping ONLY the digits; the generic caption
    ("low end" / "typical" / "high end") stays a sibling `<span>`, never
    inside the slot, so `set_text()`'s child-wipe on fill cannot delete it
    and the caption remains template furniture, positionally copied (or,
    for shapes that don't match, left as the base's own text) exactly like
    any other short unslotted string. `TK_02.content-schema.json`
    regenerated (three new row slots, `type: currency`, added to
    `SLOT_SCHEMA.json` alongside the existing `src.low`/`src.mid`/`src.high`
    convention); `TK_02.example-content.json` gives both `comp.rows` rows
    their own low/mid/high figures (posting row: 115k/135k/155k, read off
    its `bar` geometry against the market row's axis and cross-checked
    against `jd.meta`'s stated $115,000-$155,000). `jdbot.md`'s content map
    updated to require all three per row. `references/briefs/jdbot.md` is
    now stale against the source and needs a `build_briefs.py` run, not
    done here (out of this fix's scope: briefs are owned elsewhere). No
    render.py change: the existing slot/positional-copy machinery handles
    this once the slots exist; the caption round-trips because slotting
    only the digits, not the whole tick div, is what makes `set_text()` and
    `direct_text()` agree on what the slot owns.
33. **TK_07 comp-chart axis labels are now a real slot (2026-08-10, client-reported
    defect).** `comp.rows`' base row (the propulsion worked example) carried its
    dollar-range axis label (`$66–83K`) as unslotted positional text. Because that
    text lived under `MIN_SYNTHETIC_LEN` (45 chars), `render_rows`' positional-copy
    branch (`scripts/render.py`, not touched here) copied it, and each variant row's
    own unslotted label text, straight from the TEMPLATE's own example prose on
    every render, regardless of content JSON: the bar geometry moved with real
    content but the printed dollar label never did, so any role's rendered pack
    showed the propulsion demo numbers (`$66–83K`, `$105–174K`, `$112–172K`,
    `Example: $115–155K + equity`) next to a bar for a different range. The base
    row's axis-label `<div>` now carries `data-slot="comp.range"`; the three
    variant rows' now-dead label literals (including variant 2's median-tick
    label, `$138K typical`, which was already structurally unreachable because
    its row has two extra elements the base row lacks — `render_rows` clones the
    base row's shape, so that tick and its label never rendered even before this
    fix and still do not) are genericized to `range label` / `median value label`
    so no leftover dollar fiction reads as real content. `SLOT_SCHEMA.json` gains
    a `comp.range` entry (`currency_range`); `TK_07.content-schema.json` is
    regenerated from the template (the only diff is `comp.range` joining
    `comp.rows`' `row_slots`); `TK_07.example-content.json` gains `comp.range` on
    all four demo rows; `agents/calibrate.md`'s CONTENT MAP and signature-device
    note now name `comp.range` as a required per-row field. Known residual: the
    variant-2 row's structural mismatch (3 base children vs. 5 of its own) also
    means `patch_styles` never repositions its cloned label div, so that row's
    `comp.range` text renders at the base row's x-position/color rather than its
    own bar's; fixing that needs a template DOM change (matching child counts
    across `comp.rows` variants) and is out of scope here.
34. **Verbatim-furniture sweep of the remaining templates (2026-08-10).** Same
    class as items 32-33, swept across TK_01/03/04/05/06/08 plus TK_00.
    (a) TK_01 `collab.nodes`: the base row's second subcard title
    (`Materials & manufacturing`, 25 chars — under the 45-char row synthetic
    floor) was unslotted and shipped verbatim into every render; it is now
    `data-slot="node.name2"` (SLOT_SCHEMA entry `label 2-3`, schema and
    example content regenerated, `agents/sensei.md` documents the field).
    (b) TK_03 `comp.levels` variant rows 2-4 and TK_08 `logistics`
    Compensation row: dead propulsion comp literals genericized (rendered
    output byte-identical — the base rows are fully slotted, so the old
    literals never rendered; they were a trap for derivative builds).
    (c) TK_04/05/06 verified clean; TK_00 Pattern Library brought up to the
    fixed conventions (item 35) since it is the canonical copy source.
35. **Comp-chart labels now ride their bars (2026-08-10, round 2 of the
    item-32/33 fix).** Adversarial review showed the round-1 slots fixed the
    TEXT but not the GEOMETRY: label divs were absolutely positioned at
    template-frozen x-positions (the demo axis), so correctly filled labels
    could still sit far from the bars they describe, and two rows could
    assert contradictory scales. The label elements are now CHILDREN of
    their `data-bar` element (`apply_bar` moves the bar; children ride
    along), making label/bar agreement structural: TK_02 `comp.rows` prints
    `comp.low` at the bar's left edge and `comp.high` at its right
    (`comp.mid` and the frozen median marker are removed — no honest
    midpoint position exists without an axis definition); TK_07
    `comp.rows`' `comp.range` rides its bar's right edge; variant rows'
    bar-containers mirror the base's child structure so per-row style
    patching works (this also fixed TK_07 row 2 and TK_02 row 2 silently
    inheriting the base row's bar colors). TK_00's pattern 06 teaches the
    new structure. Agent contract (jdbot, calibrate): print exactly the
    values your own row's bar encodes; a label/bar mismatch is a qa-gate
    return.
36. **Renderer furniture lint + missing-row-slot blanking (2026-08-10).**
    `scripts/render.py` gains `lint-template`, wired into `schema`
    (stderr warnings + `furniture_warnings` key when non-empty) and
    `verify` (HIGH findings, labeled as TEMPLATE defects so nobody chases a
    content patch). Round-2 hardening after adversarial review: the lint
    scans every surface the renderer actually copies verbatim — rows
    repeats (using the real synthetic-promotion predicate, not a length
    proxy), nested and optional-pass repeats (which have NO synthetic pass,
    so any length is risky there), `data-optional` block text, the grid
    corner cell, points-repeat non-label text, plus an informational
    attribute tier (title/alt/aria-label). Two verify additions:
    `identical to example (risky)` (HIGH) catches short slot values left at
    the template's own example text (e.g. `105k`) that the 25-char floor of
    the existing check missed; and `render_rows` now BLANKS a missing row
    slot's direct text (still reported in `missing`) instead of leaving the
    base row's worked-example prose — item 25's guarantee ("missing content
    never leaves template example prose behind") now genuinely holds for
    every slot class, making item 31(d)'s claim true for row slots.
