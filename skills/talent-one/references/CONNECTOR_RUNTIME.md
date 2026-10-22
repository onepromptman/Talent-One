# Connector runtime

Read this when your prompt from the orchestrator lists a connector, or when ToolSearch finds one of the bundled servers. Everything here EXTENDS the public-data path; nothing here is required. A connector that is not connected is simply absent from ToolSearch: run the public layer and say nothing about it.

## 1. Discovery

Search with ToolSearch for `+exa`, `+brightdata`, `+greenhouse`, `+ashby` (the bundled servers; their tools are named `mcp__plugin_talent-one_<server>__<tool>`). Your agent file lists exactly the servers you may use; nothing else in the session reaches you (the user's own document store or ATS is read by the orchestrator at intake and filed into `inputs/` or the KB, which is where you read it). Load only the tools you will call. If ToolSearch is absent in this session, the tools are already in your list under those names. A server that fails to connect, times out, or returns an authentication error is a Class B miss: degrade honestly on the public layer, never retry in a loop, never ask the user for a token (the orchestrator owns the user channel; report the miss in your final message instead).

## 2. Tool map by source codename

| Codename (grounding matrix) | Bundled tools | Use for | Readers |
|---|---|---|---|
| `ATS` (T0) | greenhouse: the read scopes the Site Admin enabled (jobs, applications, interview stages, scorecards, users). ashby: `filter_records` asked for a count, `get_job_pipeline`, `get_interview_plan`, `get_record_details` and `search_records_by_name` for jobs, job postings and openings only | historical postings and titles; funnel actuals (HOUSE rates once n is 30 or more for the role family); scorecard fields; interview stages of record; open-req pipeline counts | scout, sensei, jdbot, hunter, interview-lab, calibrate, recruiter-screen, qa-gate |
| `TRG`, `NEWSROOM`, `EDGAR`, `AGG`, posting language (T2 and T3, web) | exa: `web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa` (date window, `includeDomains`, category `company` or `news`) | dated triggers (publish date inside 90 days), company proof points, posting language from comparable employers, comp postings for this exact title and level | scout, atlas, shakespeare, jdbot, calibrate |
| the same, when a page refuses WebFetch | brightdata: `search_engine`, `search_engine_batch`, `scrape_as_markdown`, `scrape_batch` (the server is limited to these four; no scraper, dataset, browser, or assistant tool is bundled) | search results; careers pages, newsrooms, and job boards behind bot protection | scout, atlas, hunter, jdbot |

Provenance does not change with the tool: an ATS read is Internal (T0); an Exa or Bright Data read of a government or company page is Sourced at that page's own tier. Precedence stays Part 2 of the grounding matrix. Prefer Exa over WebSearch when both are present for anything that needs a date window or a domain restriction; prefer WebFetch over Bright Data for any page that opens cleanly.

## 3. Budget

Every Exa and Bright Data call is one web call against scout's 12-call pack budget and against each artifact agent's bounded-lookup allowance, exactly like WebSearch and WebFetch. A batch call (`search_engine_batch`, `scrape_batch`, one Exa query covering a company's two or three triggers) counts as one. ATS reads are not web calls and carry no budget beyond the vendor's rate limit; do not poll or loop.

## 4. Privacy (grounding matrix Part 5, with the tools named)

- Candidate objects: counts and stage names only (`get_job_pipeline`, `filter_records` asked for a count). No candidate name, email, resume text, note, feedback, or transcript enters a pack, a content file, a handoff, or any web query. Nine Ashby tools are denied in your agent file (`get_candidate`, `get_interview_details`, `get_upcoming_interviews`, `get_submitted_feedback`, `get_pending_tasks`, and the four write tools). The Ashby tools you do have can still return a person when asked about one (`search_records_by_name` on a candidate, `filter_records` on candidates without a count, `get_record_details` on an application): never ask them that way, and if a person record arrives anyway, keep the count and discard the record. Greenhouse exposes no per-tool switch: use only its job, posting, interview-stage, scorecard-field and user reads, never a candidate, application-detail or attachment read.
- No scraper, dataset, person-profile, or people-search tool is bundled, by design (Bright Data is limited to search and page reads). Never call one from any connector for this kit.
- Internal strings, comp figures, employee names, and candidate names never go into an Exa, Bright Data, WebSearch, or WebFetch query.
- Write actions (`change_application_stage`, `create_candidate`, `add_note_to_candidate`, `consider_candidate_for_job`, any Greenhouse write scope) are never called by any Talent One agent. The Ashby ones are denied in your agent file; Greenhouse writes can only be kept off by the Site Admin's scopes and the user's consent screen, so treat any Greenhouse write tool you can see as off limits. A tool you cannot see is this rule working, not a misconfiguration.

## 5. Recording

Name every connector you actually read in `built_from` (scout) or `handoff.assumptions` (artifact agents): `greenhouse`, `ashby`, `exa`, `brightdata`, or the user's own connector name. qa-gate reads these to check pills against tiers.
