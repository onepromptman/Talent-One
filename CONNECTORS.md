# Connectors

Talent One runs with **no connections at all**: every agent has a public-data path (BLS, O*NET, Census, DOL disclosure data, levels.fyi, live web search) that is fully supported, not a degraded mode. Connecting tools upgrades specific agents.

## Bundled with the plugin

Four remote MCP servers ship in the plugin's `.mcp.json`. They load with the plugin, none needs a key to install, and a server you never sign in to just sits unused.

| Server | What it is | Sign-in | What it upgrades |
|---|---|---|---|
| `exa` | Exa web search and page reads (`web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa`) | Works keyless with free rate limits, no sign-in. To run on your own Exa plan, install Exa's own plugin (`claude plugin install exa@claude-plugins-official`) or add `https://mcp.exa.ai/mcp?login` as your own server and sign in there | Dated triggers, company proof points, posting language, comp postings: Scout, Atlas, Shakespeare, JD-Bot, Calibrate |
| `brightdata` | Bright Data remote MCP, limited to four tools: search results (`search_engine`, `search_engine_batch`) and page reads (`scrape_as_markdown`, `scrape_batch`). No scraper, dataset, browser, or assistant tool | OAuth, per user, from `/mcp` or the Connectors tab (Bright Data's hosted server is an OAuth 2.1 resource; no API key is stored anywhere in the plugin) | Careers pages, newsrooms, and job boards that refuse a plain fetch: Scout, Atlas, Hunter, JD-Bot |
| `greenhouse` | The official Greenhouse MCP server (open beta on Core, Plus, and Pro) | OAuth, per user, from `/mcp` or the Connectors tab. A Greenhouse Site Admin (with Dev Center access) enables scopes under Dev Center, MCP Access; keep write scopes off, and deselect Candidates and Attachments on the consent screen. The plugin ships Greenhouse's general URL; if Claude Code sign-in fails, Greenhouse's own Claude Code instruction uses `https://mcp.us.greenhouse.io/mcp`, which you can add with `claude mcp add` while switching the bundled one off | Historical postings and titles, funnel actuals (HOUSE rates once n is 30 or more), scorecard fields, interview stages: Scout, Sensei, JD-Bot, Hunter, Interview Lab, Calibrate, Recruiter Screen |
| `ashby` | The official Ashby MCP server (open beta, all plans) | OAuth, per user, from `/mcp` or the Connectors tab. An Ashby Org Admin turns on the MCP Server opt-in; connecting users need Elevated Access | Same as Greenhouse |

Use what you have and switch the rest off in `/mcp` (Claude Code) or the plugin's Connectors tab (Cowork). An unused server costs nothing but a row in the list.

## Your own connectors

The eleven agents reach only the four bundled servers (each agent file lists exactly the servers it may use) plus the built-in web tools; they never see the other connectors in your session, including anything that can send mail, post messages, or write records. Your own connectors still count: the orchestrator and the setup wizard run in your main session with everything you have connected, so a document store (Google Drive, Box, Notion, Confluence) or an ATS with its own server (Workable, Teamtailor, Gem, Dover, and others) is read there at intake and filed into the role's `inputs/` or the `talent-one-kb/` folder, where every agent reads it. Lever publishes no MCP server as of October 2026. Workday's Agent-Ready MCP Tools (generally available October 2026) are tenant-scoped and need Workday Extend; connect them yourself the same way.

| Category | Options | What it upgrades |
|---|---|---|
| ATS | Greenhouse, Ashby (bundled, read by agents); Workable, Teamtailor, Gem, Dover, Workday (your own, read at intake) | Historical postings, funnel actuals, scorecard fields (Scout, Sensei, JD-Bot, Hunter, Interview Lab) |
| Documents | Google Drive, Box, Notion, Confluence | Brand voice, EEO statement, benefits lines, past interview plans, calibration notes (JD-Bot, Shakespeare, Interview Lab) |
| Web research | Exa (bundled), Bright Data (bundled), native WebSearch (always works) | Deeper market research for Scout, Atlas, and Calibrate |

## Rules that hold regardless of what is connected

- Agents read ATS candidate pipelines as counts and stage names only. No candidate name, resume, note, or feedback enters a pack, a document, or a web query.
- No scraper, dataset, person-profile, or people-search tool is bundled, by design: Bright Data is limited to search and page reads.
- Talent One never writes to an ATS. Ashby's four write tools and its five candidate-bearing reads (`get_candidate`, `get_interview_details`, `get_upcoming_interviews`, `get_submitted_feedback`, `get_pending_tasks`) are denied in every agent's configuration, not just by instruction; the remaining Ashby reads can still return a candidate when asked about one, and agents are instructed to ask for counts only. Greenhouse write tools cannot be denied by the plugin: keep write scopes off in Dev Center, MCP Access and deselect Candidates and Attachments at consent. Ashby notes its tool names may change, so the denylist is reviewed each release.
- Internal strings, comp figures, employee names, and candidate names never go into a web search query.
- Every Exa and Bright Data call counts against the same 12-call research budget as a native web search, and the pack records the count.

The agent-facing rules are in `skills/talent-one/references/CONNECTOR_RUNTIME.md`.
