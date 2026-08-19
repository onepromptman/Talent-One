> **Cowork adaptation notice:** this file predates the Cowork plugin. Where it references config.yaml, out/ paths, scripts, n8n nodes, or the KB mirror workflow, `ADAPTATIONS.md` in this folder is authoritative and supersedes it.

# GROUNDING MATRIX · PER-AGENT CONTEXT ARCHITECTURE

Version 1.0 · **Authoritative over the generic research playbook inside each agent
prompt.** Each agent reads its own Part 3 block. A09 QA Gate audits provenance against
this file.

Sources are named by **role**, not by product. `[ATS]`, `[Wiki]`, `[Comp System of
Record]` and friends are slots you bind to whatever your organization actually uses at
deploy time. Binding them is a config task; the precedence rules in Part 2 do not
change when the product behind a slot changes.

---

## PART 1 · SOURCE REGISTRY

Trust tiers: **T0** internal system of record · **T1** government data · **T2** industry
primary · **T3** aggregator (triangulation only, never a sole source).

| ID | Source role | Type | Tier | Binding | Refresh |
|----|-------------|------|------|---------|---------|
| `ATS` | Applicant tracking system | LIVE SYSTEM | T0 | Read-only scopes: jobs, postings, offers, scorecards, users; candidate objects only for rediscovery queries | Live |
| `WIKI` | Internal recruiting wiki / collaboration space | LIVE SYSTEM | T0 | Space-scoped read, or a periodic export drop to `kb/internal/` | Live |
| `CSR` | **Comp System of Record**, the approved internal band | LIVE SYSTEM (export) | T0 | Band export to `kb/internal/comp/bands.csv`, keyed by a role-family crosswalk ID | Per comp cycle |
| `CSV` | **Comp Survey Vendor**, external market survey | SURVEY | T2 | Percentile lookup via the same crosswalk ID | Per survey cycle |
| `ORG` | Org / headcount system | LIVE SYSTEM | T0 | Read: org units, reporting lines, team rosters | Weekly |
| `OR` | **The Oracle**, structured benchmark reference | ORACLE | T1-T2 | `kb/benchmarks/oracle_reference.yaml`, built by the benchmark-extractor process (Part 4) from government series (labor statistics occupational series, census housing and migration tables, occupational skill profiles) and industry workforce studies | Annual, or on release |
| `MKT` | Talent-market insight export | MARKET EXPORT | T2 | Manual export drop to `kb/market/`; cite the export date | Per search kickoff |
| `TRG` | Trigger monitors: statutory layoff notice databases, layoff trackers, company newsrooms, trade press | WEB LIVE | T2 | Live search plus fetch | Live, 90-day validity |
| `AGG` | Comp aggregators | WEB LIVE | T3 | Live search plus fetch | Live, 6-month validity |
| `HX` | `history/`, prior artifacts of the same type, with measured results where known | KB | T0 | `kb/history/` retrieval | Appended every run |
| `BR` | `brand/`, voice guide, forbidden phrases, benefits summary, and the equal-opportunity statement | KB | T0 | `kb/brand/` | On change |

**`CSR` and `CSV` are two distinct roles and must stay distinguishable.** Collapsing
them into one "comp source" label destroys the Part 2 precedence rule that depends on
telling an approved internal band apart from an external survey percentile.

---

## PART 1.5 · PUBLIC DATA SOURCES (THE STANDALONE LAYER)

The T0 rows above assume an organization with internal systems. **This pack must also
run for a search that has none**, so every quantitative claim an agent needs has a named
public source here. Bind these once; agents cite them by codename.

### T1 · Government and official series

| Code | Source | Grounds | Access |
|---|---|---|---|
| `BLS-OES` | BLS Occupational Employment and Wage Statistics | National and metro employment counts and wage percentiles by occupation. **The supply-funnel baseline.** | `api.bls.gov/publicAPI/v2` · series by SOC code |
| `BLS-OOH` | BLS Occupational Outlook Handbook | 10-year growth projections, entry-level education, occupation description | `bls.gov/ooh` |
| `BLS-JOLTS` | BLS Job Openings and Labor Turnover Survey | Openings, hires, quits, and layoffs by sector. **The demand-side and market-tightness anchor.** | `api.bls.gov/publicAPI/v2` |
| `BLS-CES` | BLS Current Employment Statistics | Sector employment levels and trend | `api.bls.gov/publicAPI/v2` |
| `ACS` | Census American Community Survey | Relocation propensity inputs: `B25003` tenure/homeownership, `B25077` median home value, `B19013` median household income, per metro | `api.census.gov/data` |
| `CENSUS-MIG` | Census county-to-county migration flows | Where this workforce actually moves, and in what volume | `census.gov/topics/population/migration` |
| `ONET` | O*NET OnLine | Skills, tasks, abilities, and tools per occupation. **The skills baseline and the adjacency test for peripheral pools.** | `services.onetcenter.org/ws` |
| `WARN` | State WARN Act notice databases | Dated statutory layoff filings. **The highest-trust trigger event: a filing, not a rumor.** | Per-state labor department pages |
| `OFLC` | DOL OFLC disclosure data (LCA / PERM) | Employer-level filed wages by job title and worksite. **Public, employer-specific, and dated: the best free comp triangulation that exists.** | `flag.dol.gov/programs/disclosuredata` |
| `FRED` | Federal Reserve Economic Data | Macro labor series for context, never for role-level claims | `api.stlouisfed.org/fred` |
| `EDGAR` | SEC EDGAR | Company proof points: filings, headcount disclosures, financial condition | `data.sec.gov` |

### T2 · Industry primary research

| Code | Source | Grounds |
|---|---|---|
| `LAYOFFS` | layoffs.fyi and equivalent trackers | Trigger events at companies below the WARN threshold |
| `HIRINGLAB` | Indeed Hiring Lab | Posting volume and competition indices by occupation and metro |
| `LIGHTCAST` | Lightcast (Burning Glass) labor-market data | Posting-level demand, skill co-occurrence, employer competitor sets |
| `LTI` | LinkedIn Talent Insights | Supply by metro, company-to-company talent flows, hiring velocity |
| `SO-SURVEY` | Stack Overflow Developer Survey | Technology adoption, comp by stack, and motivators, for software roles |
| `SHRM-BM` | SHRM talent-acquisition benchmarking | Time-to-fill, cost-per-hire, interviews-per-hire baselines |
| `GEM-BM` | Gem recruiting benchmarks | Outbound reply rates, sequence performance, funnel pass-through |
| `NEWSROOM` | Company newsrooms and named trade press | Dated proof points and trigger events |

### T3 · Aggregators (triangulation only, never a sole source)

| Code | Source | Note |
|---|---|---|
| `LEVELS` | levels.fyi | Strongest of the T3 set for leveled tech comp; still self-reported |
| `GLASSDOOR` · `SALARY` · `ZIP` · `PAYSCALE` | Comp aggregators | Self-reported, unverified sample. Use to bracket a range, never to set one |

### Rules for the public layer

1. **Cite the codename and the vintage.** `Sourced · BLS-OES 2024`, not `Sourced`.
2. **`BLS-OES` is the funnel baseline.** Every derived funnel stage below it is an
   Estimate with a stated filter and basis, per A03's methodology.
3. **`OFLC` is public and employer-specific.** It is the one free source that gives a
   named employer's filed wage for a named title. Prefer it over any T3 aggregator when
   the question is "what does *that company* pay".
4. **`WARN` outranks `LAYOFFS`.** A statutory filing is dated and verifiable; a tracker
   entry is a lead. An undated rumor is unusable at any tier.
5. **Never quote a T3 figure alone.** Two independent T3 sources that agree is an
   Estimate. One T3 source is not evidence.
6. When the public layer and an internal T0 system disagree, Part 2 governs: internal
   wins, the public finding is added, and a Caution callout is raised.

---

## PART 2 · SOURCE-OF-TRUTH PRECEDENCE

When two sources answer the same question, the higher row wins. Lower rows may
triangulate or raise a Caution callout, never silently override.

| Data type | Precedence order |
|---|---|
| Comp band / posted range | `CSR` approved band > `CSV` percentile (via crosswalk) > `ATS` accepted-offer actuals > `AGG` (triangulation only) |
| Titles and synonyms | `ATS` historical postings > `WIKI` internal lists > SENSEI web extension |
| Interview process, rubrics, interviewer names | `WIKI` verbatim > `ATS` scorecard config > never web, never invented |
| Funnel and outreach rates | House actuals from `ATS` (when n ≥ 30 for the role family) > `OR` benchmarks > web claims |
| Occupation counts, demographics, homeownership, migration | `OR` (government series) > web estimates, Estimate-pilled |
| Trigger events | `TRG` dated primary (statutory filing, newsroom, named outlet) > aggregator mention > undated rumor (unusable) |
| Company proof points | Company newsroom or regulatory filing > trade press > never memory |
| Voice and structure | `BR` + `HX` exemplar of the same artifact type > model default |

---

## PART 3 · PER-AGENT CONTEXT BLOCKS

Format: source, what it grounds, retrieval pattern, then the consistency anchor.

### A07 CALIBRATE → `TK_07`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `ATS` | Intake notes; historical time-to-hire and accepted-offer comp for this role family; interviews-per-hire actuals | Current req plus last 5 closed reqs in the same team; offers by level |
| `CSR` | The internal comp anchor in Section B | Band lookup by crosswalk ID; aggregators become the market spread *around* it |
| `WIKI` | Calibration boundary questions (Section E), documented requirements (Section F) | `"{role} hiring guide"`, `"{role} calibration"` |
| `OR` | Section A macro stats (shortage rate, attrition, cost of vacancy, workforce age) | Metric category `workforce_macro` |
| `TRG` | Section C timing windows | Statutory-notice and newsroom sweep across the top 3 comparable employers, 90-day window |

**Consistency anchor:** `HX` prior calibration pack for the same role family. SLA table
values are org standards, never re-derived per run.

### A01 SENSEI → `TK_01`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `WIKI` | Role overview, responsibilities, internal synonym list | `"{role} internal summary"`, `"{role} synonymous titles"` |
| `ATS` | Language mining: how this team actually describes itself | Last 3 postings from the same team |
| `ORG` | Collaboration map: real adjacent teams and the hiring manager | Org-unit query for the team node |
| `OR` | Skills baseline sanity check | Occupational skill profile for the occupation |

**Consistency anchor:** `HX` prior briefs: reuse the metaphor-engine style. One
load-bearing analogy per role, never recycled across different roles.

### A03 ATLAS → `TK_03`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `OR` | Funnel baseline (occupation count), homeownership and housing tables, macro demand stats, funnel benchmarks | Categories `occupation_counts`, `geo_acs`, `workforce_macro`, `funnel` |
| `MKT` | Supply by metro, demand postings, company-to-company talent flows | Export for the role's title cluster; cite the export date |
| `ATS` | Ground truth: source-of-hire by company, pipeline pass rates per source company, accepted-offer actuals | Aggregation by role family; feeds tier poach ratings and the comp table |
| `WIKI` | No-go and cautious employer flags | `"no-go"`, `"do not source"` |
| `TRG` | Section 5 triggers, all dated | Per tier-1 employer |
| `AGG` | Comp triangulation only | Standard aggregator sweep |

**Consistency anchor:** `HX` prior talent maps. Funnel filter percentages persist
run-to-run; any change requires a stated justification line in the methodology table
(drift detection). Tier assignments diff against the prior map, changes logged in an
Insight callout.

### A02 JD-BOT → `TK_02`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `ATS` | Voice and structure corpus: last 3-5 postings in the team; the org's best-converting postings; the previous posting of *this* role if it exists | Postings by team, sorted by apply-to-screen conversion where available |
| `BR` | The equal-opportunity statement and current benefits lines, verbatim | Direct file read |
| `CSR` | Posted range | Band lookup. Never a web-derived range when a band exists |
| Handoffs | Requirements (CALIBRATE), pool-math rationale for nice-to-haves (ATLAS), titles and synonyms (SENSEI) | JSON only |

**Consistency anchor:** Mirror the structure of the best-converting historical posting.
Produce a change-diff line in the calibration ledger against the previous posting of the
same role: what changed, and what it costs in pool.

### A04 HUNTER → `TK_04`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `ATS` | House funnel actuals (replace `OR` rates when n ≥ 30); rediscovery pool (past onsite candidates, adjacent roles); source-of-hire channel mix | Pipeline aggregation plus rediscovery query |
| `OR` | Benchmark rates where house n < 30; outreach sequence benchmarks | Categories `funnel`, `outreach` |
| `MKT` | Search-string result-size sanity checks | Compare against expected-result estimates |
| `HX` | Versioned string library with past performance | Reuse winning strings, increment the version tag |

**Consistency anchor:** Pipeline math states which rates are HOUSE and which are ORACLE,
per row. The string library is append-only with version tags.

### A05 SHAKESPEARE → `TK_05`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `BR` | Voice, forbidden phrases, sign-off conventions | Direct read |
| Handoffs | Hiring-manager pitch verbatim (CALIBRATE), personas and value props (HUNTER **and** ATLAS directly) | JSON only |
| `TRG` | Verify every proof point before it enters copy | Newsroom fetch |
| `HX` | Past sequences with measured reply rates | Reuse A/B winners, retire losers |

**Consistency anchor:** A/B winners persist across runs; a new variant may replace a
control, never both arms. Candidate personal data never enters copy-generation context.

### A06 INTERVIEW LAB → `TK_06`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `WIKI` | Interview plan, questions of record, protocol rules, scoring rubric verbatim, values definitions | `"{role} interview plan"`, `"scoring rubric"`, `"values"` |
| `ATS` | Scorecard attributes: the competency matrix must align to real scorecard fields; interviewer tags for the pool | Scorecard config for the role family |
| `ORG` | Interviewer pool validation: still employed, still on the team | Roster check before any name prints |

**Consistency anchor:** Matrix competencies must be a superset of `ATS` scorecard
attributes. A mismatch surfaces as a Caution callout, never silent invention.

### A08 RECRUITER SCREEN → `TK_08`

| Source | Grounds | Retrieval pattern |
|---|---|---|
| `WIKI` | Calibrated questions and graded tiers | `"screen questions"`, `"answer rubric"` |
| `ATS` | Private-notes fields mirror the actual screen template fields | Screen-stage template for the role family |
| Handoffs | Comp line and constraints (CALIBRATE `comp_frame`, `constraints[]`); skills to spot-check and title synonyms (SENSEI) | JSON only |

**Consistency anchor:** Respect tier structure and meaning; normalize informal internal
wording for readability and cite the source. Author-generated additions capped at one
question.

### A09 QA GATE → no template

Reads everything, plus this file. Additional audits beyond the shared-core self-QA list:

1. **Provenance-to-source mapping.** Every Sourced pill must trace to a registry source
   at or above the Part 2 precedence row for its data type. A comp figure pilled to an
   aggregator while a `CSR` band exists is a FAIL.
2. HOUSE vs ORACLE labeling present in pipeline math.
3. `ATS`-derived names cross-checked against the `ORG` roster before printing.
4. Drift log present in ATLAS when funnel values changed.
5. No candidate personal data anywhere in outreach artifacts.
6. Handoff schema conformance against Part 3.5 below, both JSON keys and the rendered
   `handoff.produces` slot.

---

## PART 3.5 · CONSOLIDATED HANDOFF SCHEMA (THE AUDIT API)

> **Talent One 1.0:** the Context Pack (`CONTEXT_PACK.md`) is the runtime data path;
> no agent reads another's handoff to build content. This table survives as the
> audit vocabulary (each agent's content JSON `handoff.keys`), the compat
> handoffs.json format the renderer derives, and the migration mapping for legacy
> runs (`CONTEXT_PACK.md` §7). Key names stay binding for those three uses.

One table for the whole network. **Every agent conforms to this; no agent invents its
own key names.** The renderer derives `handoff.produces` from these keys in this
order, `·`-separated.

| Producer | Consumers | Exact keys in `handoff` | Budget |
|---|---|---|---|
| A07 CALIBRATE | A01, A02, A03, A04, A05, A06, A08 | `requirements[]` (each `{name, verdict, verified_by}`) · `comp_frame` · `timing_windows[]` · `tradeoff_lock` · `constraints[]` · `sla` | ≤300 tok |
| A01 SENSEI | A02, A03, A06, A08 | `primary_keywords[]` · `title_synonyms[]` · `cross_industry_pools[]` · `skill_transfer_notes[]` · `seniority_ladder` · `must_have_skills[]` | ≤300 tok |
| A03 ATLAS | A02, A04, A05 | `market` · `funnel` · `comp_guidance` · `tier1_targets[]` · `peripheral[]` · `geo_sequence[]` · `personas[]` · `market_urgency` · `comp_messaging` · `pain_point_angles[]` · `cross_industry_pools[]` · `skill_transfer_notes[]` | ≤350 tok |
| A02 JD-BOT | A04, A09 | `must_have_skills[]` · `nice_to_have[]` · `years_experience` · `education` · `posted_range` · `assessment_methods[]` | ≤300 tok |
| A04 HUNTER | A05 | `personas[]` · `search_strings[]` · `channel_mix[]` · `pipeline_math` · `target_companies[]` | ≤350 tok |
| A06 INTERVIEW LAB | A09 | `stages[]` · `competency_coverage` · `deal_breakers[]` · `debrief_protocol` | ≤300 tok |
| A08 RECRUITER SCREEN | A09 | `grades` · `motivators_verbatim[]` · `flags[]` · `recommendation` | ≤250 tok |
| A05 SHAKESPEARE | A09 | `sequence[]` · `channels[]` · `ab_variants[]` · `banned_phrases_checked` | ≤250 tok |
| A09 QA GATE | orchestrator | `verdict` · `findings[]` (each `{artifact, agent, check, severity, evidence, required_fix}`) | ≤400 tok |

**`assumptions` is a sanctioned extra key, not a producer-specific one.** Any producer
may add `assumptions` to its JSON `handoff` object when `00_SHARED_CORE.md` §6.5's
degraded-proceed rule or `ADAPTATIONS.md` item 13's seeding rule applies. It is exempt
from the `handoff.produces` match: never list it in `handoff.produces`, and A09 does
not count it as a schema mismatch. Where the bound template carries a
`handoff.assumptions` slot, render the same text there; where it does not (TK_03,
TK_04, TK_05), the JSON key alone carries it. Absent, omit the key entirely rather
than emitting it empty.

**Relay note (historical).** The 0.9.x SENSEI-through-ATLAS relay for
`cross_industry_pools` and `skill_transfer_notes` no longer exists at runtime: both
fields live in the pack (`keywords.*`) and every agent reads them there. Atlas and
Sensei still carry them in their audit keys unchanged.

---

## PART 4 · THE ORACLE BUILD SPEC

`kb/benchmarks/oracle_reference.yaml`, built by the benchmark-extractor process from the
whitepaper set plus government series. Schema per metric:

```yaml
- metric: outbound_reply_rate_3stage
  value: "26%+"
  category: outreach       # workforce_macro | funnel | outreach | comp | occupation_counts | geo_acs | skills
  source: "<publisher>, <report title>"
  year: 2025
  location: "p.77"
  applies_to: all_roles    # or a role-family key
  as_of: 2025-01
  confidence: HIGH         # HIGH | MEDIUM | LOW
```

`confidence` grades how directly the source supports the metric: HIGH = stated outright
in the source; MEDIUM = derived from stated figures; LOW = inferred across sources or
from a small sample. Agents surface LOW-confidence figures as Estimates regardless of
the source's tier.

Rules: one entry per metric per source (conflicts are allowed and agents cite both);
`as_of` drives the freshness SLAs; government entries store their table or series IDs so
refresh is scriptable; **rerun the extractor on every new source drop. This is a
mandatory pre-deployment step, not an optional one.** A benchmark dropped into `kb/`
without an extractor pass is invisible to the pack.

### Source register: what the extractor ingests

The recurring documents and series the Oracle is built from, so agents cite a stable
codename rather than re-deriving a citation per run. Codenames match Part 1.5.

| Codename | What it yields | Categories | Refresh |
|---|---|---|---|
| `BLS-OES` | Employment counts and wage percentiles by SOC and metro | `occupation_counts`, `comp` | On release, annual |
| `BLS-OOH` | Growth projection, entry education, occupation description | `occupation_counts`, `skills` | Annual |
| `BLS-JOLTS` | Openings, hires, quits, layoffs by sector | `workforce_macro` | Monthly |
| `ACS` | `B25003` tenure · `B25077` home value · `B19013` income, per metro | `geo_acs` | Annual |
| `CENSUS-MIG` | County-to-county migration volumes | `geo_acs` | Annual |
| `ONET` | Skills, tasks, tools, and abilities per occupation | `skills` | On release |
| `OFLC` | Employer-level filed wages by title and worksite | `comp` | Quarterly |
| `HIRINGLAB` | Posting volume and competition index by occupation and metro | `workforce_macro`, `funnel` | Monthly |
| `SHRM-BM` | Time-to-fill, cost-per-hire, interviews-per-hire | `funnel` | Annual |
| `GEM-BM` | Outbound reply rates and sequence performance | `outreach` | Annual |
| `SO-SURVEY` | Stack adoption, comp by technology, motivators | `skills`, `comp` | Annual |
| `LIGHTCAST` | Posting-level demand, skill co-occurrence, competitor sets | `workforce_macro`, `skills` | Licensed, per refresh |
| `LTI` | Supply by metro, talent flows, hiring velocity | `occupation_counts` | Per search kickoff |

Populate `location` in each Oracle entry with the table ID, series ID, or page number so
a refresh is scriptable and a reviewer can check the figure at its source.

### Per-agent public-source fallback

When no internal T0 system is bound, agents run on the public layer alone. This is the
supported standalone path, not a degraded mode:

| Agent | Public sources |
|---|---|
| A07 CALIBRATE | `BLS-OES` · `OFLC` · `LEVELS` · `BLS-JOLTS` · `WARN` · `LAYOFFS` |
| A01 SENSEI | `ONET` · `BLS-OOH` · `SO-SURVEY` |
| A03 ATLAS | `BLS-OES` · `BLS-JOLTS` · `ACS` · `CENSUS-MIG` · `HIRINGLAB` · `LIGHTCAST` · `WARN` · `LAYOFFS` · `EDGAR` · `NEWSROOM` |
| A02 JD-BOT | `BLS-OES` · `ONET` · public postings from comparable employers |
| A04 HUNTER | `GEM-BM` · `SHRM-BM` · `LIGHTCAST` · `LTI` |
| A05 SHAKESPEARE | `GEM-BM` · `NEWSROOM` · `LAYOFFS` · `SO-SURVEY` |
| A06 INTERVIEW LAB | `ONET` (competency derivation) · `SHRM-BM` (loop length norms) |
| A08 RECRUITER SCREEN | `ONET` · A07 and A01 handoffs |

---

## PART 5 · ACCESS, SCOPES, AND SENSITIVE-DATA ROUTING

- **`ATS`**: read-only, scoped to jobs, postings, offers, scorecards, users. Candidate
  object access limited to rediscovery queries. Candidate personal data is never passed
  into SHAKESPEARE's context and never leaves T0 systems.
- **`WIKI`**: recruiting space, read-only. A periodic export is the fallback wherever
  live access is not approved.
- **Comp**: `bands.csv` is the only comp artifact in `kb/`. Raw survey files stay in
  whatever enclave the comp team keeps them in. The crosswalk ID is the only join key
  agents ever see.
- **Routing rule**: T0 system data flows into artifacts only, never into a web tool
  call. No internal string, band figure, employee name, or candidate name may appear
  inside a web search query.
- **Constraints**: `config.constraints[]` describes *requirements*, not people. An
  agent may quote a constraint's text and may report whether an individual candidate
  answered yes or no at their gate stage. An agent may never estimate the size of a
  protected-class or nationality-linked population, and may never infer an individual's
  status from anything other than their own answer.
