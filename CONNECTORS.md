# Connectors

## How tool references work

Talent One works out of the box with **no connections at all**: every agent has a public-data path (BLS, O*NET, Census, DOL disclosure data, levels.fyi, live web search) that is fully supported, not a degraded mode.

Connecting tools upgrades specific agents. Plugin files use `~~category` as a placeholder for whatever tool you connect in that category.

## Connectors for this plugin

| Category | Placeholder | Options | What it upgrades |
| --- | --- | --- | --- |
| ATS | `~~ats` | Greenhouse, Ashby, Lever, Workday | Historical postings, funnel actuals, scorecard fields (Sensei, JD-Bot, Hunter, Interview Lab) |
| Documents | `~~docs` | Google Drive, Box, Notion, Confluence | Brand voice, EEO statement, past interview plans, calibration notes (JD-Bot, Shakespeare, Interview Lab) |
| Web research | `~~research` | Tavily, native web search | Deeper market research for Atlas and Calibrate (native WebSearch always works) |
| Enrichment | `~~enrichment` | LeadMagic, Apollo | Company and people enrichment for talent mapping (Atlas, Hunter) |

Rule that always holds regardless of connections: internal strings, comp figures, employee names, and candidate names never go into a web search query.
