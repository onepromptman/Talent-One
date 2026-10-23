# Connectors

Talent One runs with **no connections at all**: every agent has a public-data path (BLS, O*NET, Census, DOL disclosure data, levels.fyi, live web search) that is fully supported, not a degraded mode. Connecting tools upgrades specific agents.

## Bundled with the plugin

Four remote MCP servers ship in the plugin's `.mcp.json`. All four sign in with OAuth, so nothing is sent to any of them until you do. In Claude Code they are registered when the plugin is enabled and show "needs authentication" in `/mcp` until you sign in; in Cowork, installing the plugin does not add them, so open the plugin's Connectors tab and add each one you want, then sign in (on Team and Enterprise plans an Owner adds connectors for the organization). The server entries in the agent files need Claude Code 2.1.300 or later; on an older client the agents simply keep the built-in web tools.

| Server | What it is | Sign-in | What it upgrades |
|---|---|---|---|
| `exa` | Exa web search and page reads (`web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa`) | OAuth, per user (the bundled URL carries Exa's `?login` flag, which Exa recommends for plugins). A free Exa account works; usage runs on your Exa plan | Dated triggers, company proof points, posting language, comp postings: Scout, Atlas, Shakespeare, JD-Bot, Calibrate |
| `brightdata` | Bright Data remote MCP, limited to four tools: search results (`search_engine`, `search_engine_batch`) and page reads (`scrape_as_markdown`, `scrape_batch`). No scraper, dataset, browser, or assistant tool | OAuth, per user, against an existing Bright Data account (5,000 free requests a month at the time of writing; no API key is stored in the plugin) | Careers pages, newsrooms, and job boards that refuse a plain fetch: Scout, Atlas, Hunter, JD-Bot |
| `greenhouse` | The official Greenhouse MCP server (open beta on Core, Plus, and Pro) | OAuth, per user. A Site Admin connects first and sets scopes under Dev Center, MCP Access (Dev Center changes need developer permissions; access may be priced, ask your account team). Greenhouse's default scopes are read-only but include candidates, applications and scorecards, so keep write scopes off and deselect Candidates and Attachments on the consent screen. The plugin ships the URL Greenhouse gives for Claude; Greenhouse's Claude Code instruction uses the US host `https://mcp.us.greenhouse.io/mcp`, which you can add with `claude mcp add` if you prefer it | Historical postings and titles, funnel actuals (HOUSE rates once n is 30 or more), scorecard fields, interview stages: Scout, JD-Bot, Hunter, Interview Lab, Calibrate (the other agents get ATS facts through the pack) |
| `ashby` | The official Ashby MCP server (open beta, all plans) | OAuth, per user. An Ashby Org Admin turns on the MCP Server opt-in; connecting users need Elevated Access; not available to Analytics-only organizations | Same as Greenhouse |

Use what you have and switch the rest off in `/mcp` (Claude Code) or leave them unadded (Cowork). An unused server costs a row in `/mcp` and a startup notice, nothing more.

## Your own connectors

The eleven agents reach only the four bundled servers (each agent file lists the Ashby tools it may use by exact name, and Exa, Bright Data and Greenhouse by server; the Exa and Bright Data URLs already limit those servers to a fixed tool list) plus the built-in web tools; they never see the other connectors in your session, including anything that can send mail, post messages, or write records. Your own connectors still count: the orchestrator and the setup wizard run in your main session with everything you have connected, so a document store (Google Drive, Box, Notion, Confluence) or an ATS with its own server (Workable, Teamtailor, Gem, Dover, and others) is read there at intake and filed into the role's `inputs/` or the `talent-one-kb/` folder, where every agent reads it. We found no official Lever MCP server as of October 2026 (community servers wrap the Lever API with an API key). Workday's Agent-Ready MCP Tools (generally available 13 October 2026) are tenant-scoped, need Workday Extend, include write tools, and require your Workday admin to register the agent in the Agent System of Record: an admin project, not a one-click connector.

| Category | Options | What it upgrades |
|---|---|---|
| ATS | Greenhouse, Ashby (bundled, read by agents); Workable, Teamtailor, Gem, Dover, Workday (your own, read at intake) | Historical postings, funnel actuals, scorecard fields (Scout, JD-Bot, Hunter, Interview Lab, Calibrate) |
| Documents | Google Drive, Box, Notion, Confluence | Brand voice, EEO statement, benefits lines, past interview plans, calibration notes (JD-Bot, Shakespeare, Interview Lab) |
| Web research | Exa (bundled), Bright Data (bundled), native WebSearch (always works) | Deeper market research: Exa for Scout, Atlas, Shakespeare, JD-Bot, Calibrate; Bright Data for Scout, Atlas, Hunter, JD-Bot |

## Rules that hold regardless of what is connected

- Agents read ATS candidate pipelines as counts and stage names only. No candidate name, resume, note, or feedback enters a pack, a document, or a web query.
- No structured-data scraper, dataset, person-profile, or people-search tool is bundled: Bright Data is limited to search results and page reads. Exa's search tools can return public profile pages if asked with its people category; agents are instructed never to ask that way.
- Talent One never writes to an ATS. Every agent that can see Ashby is allowed exactly six Ashby read tools by name (`search_records_by_name`, `filter_records`, `describe_object_fields`, `get_record_details`, `get_job_pipeline`, `get_interview_plan`); the write tools, `get_candidate`, the interview, feedback and task tools, and anything Ashby adds later (Ashby says it adds tools, including writes, over time, and that inputs and outputs may change without notice) are invisible to agents. Those six reads can still return a candidate when asked about one, so agents are instructed to ask for counts only. The plugin does not block Greenhouse tools one by one (about 150 tools whose names can change): keep write scopes off in Dev Center, MCP Access and deselect Candidates and Attachments at consent.
- Internal strings, comp figures, employee names, and candidate names never go into a web search query.
- Every Exa and Bright Data call counts against the same 12-call research budget as a native web search, and the pack records the count.

The agent-facing rules are in `skills/talent-one/references/CONNECTOR_RUNTIME.md`.
