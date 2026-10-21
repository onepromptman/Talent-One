# Connectors

Talent One runs with **no connections at all**: every agent has a public-data path (BLS, O*NET, Census, DOL disclosure data, levels.fyi, live web search) that is fully supported, not a degraded mode. Connecting tools upgrades specific agents.

## Bundled with the plugin

Four remote MCP servers ship in the plugin's `.mcp.json`. They load with the plugin, none needs a key to install, and a server you never sign in to just sits unused.

| Server | What it is | Sign-in | What it upgrades |
|---|---|---|---|
| `exa` | Exa web search and page reads (`web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa`) | Works keyless with free rate limits. Sign in once (`/mcp` in Claude Code, the plugin's Connectors tab in Cowork) to run on your own Exa plan | Dated triggers, company proof points, posting language, comp postings: Scout, Atlas, Shakespeare, JD-Bot, Calibrate |
| `brightdata` | Bright Data remote MCP, scoped to six read tools: search results, bot-protected page reads, LinkedIn company profiles and job listings | OAuth, per user, from `/mcp` or the Connectors tab (Bright Data's hosted server is an OAuth 2.1 resource; no API key is stored anywhere in the plugin) | Careers pages and job boards that refuse a plain fetch; employer headcount and specialties for dossiers; live posting demand: Scout, Atlas, Hunter, JD-Bot |
| `greenhouse` | The official Greenhouse MCP server (open beta on Core, Plus, and Pro) | OAuth, per user, from `/mcp` or the Connectors tab. A Greenhouse Site Admin enables read scopes under Dev Center, MCP Access | Historical postings and titles, funnel actuals (HOUSE rates once n is 30 or more), scorecard fields, interview stages: Scout, Sensei, JD-Bot, Hunter, Interview Lab, Calibrate, Recruiter Screen |
| `ashby` | The official Ashby MCP server (open beta, all plans) | OAuth, per user, from `/mcp` or the Connectors tab. An Ashby Org Admin turns on the MCP Server opt-in | Same as Greenhouse |

Use what you have and switch the rest off in `/mcp` (Claude Code) or the plugin's Connectors tab (Cowork). An unused server costs nothing but a row in the list.

## Your own connectors

Agents inherit every MCP connector in your session, so a document store (Google Drive, Box, Notion, Confluence) or an ATS with its own server (Workable, Teamtailor, Gem, Dover, and others) works without any plugin change: connect it in `/mcp` or in Cowork's Connectors, and `set up talent one` records it in the profile. Lever and Workday publish no MCP server as of October 2026; third-party connectors exist, and the public-data path covers the rest.

| Category | Options | What it upgrades |
|---|---|---|
| ATS | Greenhouse, Ashby (bundled); Workable, Teamtailor, Gem, Dover (your own) | Historical postings, funnel actuals, scorecard fields (Scout, Sensei, JD-Bot, Hunter, Interview Lab) |
| Documents | Google Drive, Box, Notion, Confluence | Brand voice, EEO statement, benefits lines, past interview plans, calibration notes (JD-Bot, Shakespeare, Interview Lab) |
| Web research | Exa (bundled), Bright Data (bundled), native WebSearch (always works) | Deeper market research for Scout, Atlas, and Calibrate |

## Rules that hold regardless of what is connected

- Agents read ATS candidate pipelines as counts and stage names only. No candidate name, resume, note, or feedback enters a pack, a document, or a web query.
- No LinkedIn person-profile or people-search tool is bundled, by design.
- Talent One never writes to an ATS. Every bundled server is used read-only. Ashby's write and candidate-record tools (`change_application_stage`, `create_candidate`, `add_note_to_candidate`, `consider_candidate_for_job`, `get_candidate`) are denied in every agent's configuration, not just by instruction. Greenhouse exposes only the scopes a Site Admin enables (read-only by default) and lets each user deselect Candidates and Attachments at sign-in; do both.
- Internal strings, comp figures, employee names, and candidate names never go into a web search query.
- Every Exa and Bright Data call counts against the same 12-call research budget as a native web search, and the pack records the count.

The agent-facing rules are in `skills/talent-one/references/CONNECTOR_RUNTIME.md`.
