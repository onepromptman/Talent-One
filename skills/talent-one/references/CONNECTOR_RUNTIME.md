# Connector runtime

Read this when your prompt from the orchestrator lists a connector, or when ToolSearch finds one of the bundled servers. Everything here EXTENDS the public-data path; nothing here is required. A connector that is not connected is simply absent from ToolSearch: run the public layer and say nothing about it.

## 1. Discovery

Search with ToolSearch for `+exa`, `+brightdata`, `+greenhouse`, `+ashby` (the bundled servers; their tools are named `mcp__plugin_talent-one_<server>__<tool>`) and for the names the orchestrator lists for the user's own connectors (a document store, a different ATS). Load only the tools you will call. A server that fails to connect, times out, or returns an authentication error is a Class B miss: degrade honestly on the public layer, never retry in a loop, never ask the user for a token (the orchestrator owns the user channel; report the miss in your final message instead).

## 2. Tool map by source codename

| Codename (grounding matrix) | Bundled tools | Use for | Readers |
|---|---|---|---|
| `ATS` (T0) | greenhouse: the read scopes the Site Admin enabled (jobs, applications, interview stages, scorecards, users). ashby: `search_records_by_name`, `filter_records`, `get_record_details`, `get_job_pipeline`, `get_interview_plan` | historical postings and titles; funnel actuals (HOUSE rates once n is 30 or more for the role family); scorecard fields; interview stages of record; open-req pipeline counts | scout, sensei, jdbot, hunter, interview-lab, calibrate, recruiter-screen, qa-gate |
| `TRG`, `NEWSROOM`, `EDGAR`, `AGG`, posting language (T2 and T3, web) | exa: `web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa` (date window, `includeDomains`, category `company` or `news`) | dated triggers (publish date inside 90 days), company proof points, posting language from comparable employers, comp postings for this exact title and level | scout, atlas, shakespeare, jdbot, calibrate |
| the same, when a page refuses WebFetch | brightdata: `search_engine`, `search_engine_batch`, `scrape_as_markdown`, `scrape_batch` | SERP results; careers pages, newsrooms, and job boards behind bot protection | scout, atlas, hunter, jdbot |
| `LTI` and `LIGHTCAST` equivalents (T3) | brightdata: `web_data_linkedin_company_profile`, `web_data_linkedin_job_listings` | employer headcount, HQ, and specialties for dossiers; live posting demand and language for comparable employers | scout, atlas, jdbot, hunter |

Provenance does not change with the tool: an ATS read is Internal (T0); an Exa or Bright Data read of a government or company page is Sourced at that page's own tier; a LinkedIn company figure is a T3 aggregator value, Estimate unless a second source agrees. Precedence stays Part 2 of the grounding matrix. Prefer Exa over WebSearch when both are present for anything that needs a date window or a domain restriction; prefer WebFetch over Bright Data for any page that opens cleanly.

## 3. Budget

Every Exa and Bright Data call is one web call against scout's 12-call pack budget and against each artifact agent's bounded-lookup allowance, exactly like WebSearch and WebFetch. A batch call (`search_engine_batch`, `scrape_batch`, one Exa query covering a company's two or three triggers) counts as one. ATS reads are not web calls and carry no budget beyond the vendor's rate limit; do not poll or loop.

## 4. Privacy (grounding matrix Part 5, with the tools named)

- Candidate objects: counts and stage names only (`get_job_pipeline`, `filter_records` asked for a count). No candidate name, email, resume text, note, feedback, or transcript enters a pack, a content file, a handoff, or any web query. `get_candidate` and the Greenhouse candidate and attachment scopes are not for this kit; if a tool returns a person record anyway, keep the count and discard the record.
- No LinkedIn person-profile or people-search tool is bundled, by design. Never call one from any connector for this kit.
- Internal strings, comp figures, employee names, and candidate names never go into an Exa, Bright Data, WebSearch, or WebFetch query.
- Write actions (`change_application_stage`, `create_candidate`, `add_note_to_candidate`, `consider_candidate_for_job`, any Greenhouse write scope) are never called by any Talent One agent. The Ashby ones, and `get_candidate`, are denied in every agent file's `disallowedTools`; a tool you cannot see is this rule working, not a misconfiguration.

## 5. Recording

Name every connector you actually read in `built_from` (scout) or `handoff.assumptions` (artifact agents): `greenhouse`, `ashby`, `exa`, `brightdata`, or the user's own connector name. qa-gate reads these to check pills against tiers.
