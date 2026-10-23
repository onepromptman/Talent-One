# Talent One 1.1.3 - Release Notes (public)

A Claude plugin: eleven coordinated talent-acquisition agents (eight document
specialists plus relay, scout, and QA gate) that turn one role brief into a
full 8-document hiring package as styled, self-contained HTML.

Runs in Claude Code and Cowork (the Claude desktop app). It does not run in
the regular Claude chat window, which cannot spawn the kit's sub-agents.

1.1.3 hardens the four bundled connectors after an independent review of the
1.1.0 connector work (three verifiers: the release claims against the code,
every vendor fact against the vendor's own documentation, and a whole-tree
consistency sweep). Documents, templates and content schemas are unchanged.

Fixed

- Bright Data is limited to four tools (search results and page reads). The
  earlier list named tools Bright Data removed on 2026-10-11; old names in the
  URL silently enable its whole scraper group, LinkedIn person scrapers
  included.
- Exa now signs in like the other three connectors (Exa's own `?login` flag
  for plugins). The earlier URL was keyless, so research queries reached Exa
  before any sign-in. Nothing is sent to any connector until you sign in.
- Least privilege, fail closed: the five agents that query an ATS hold an
  exact-name allowlist of six Ashby read tools; writes, candidate records and
  anything Ashby adds later are invisible. Sensei, Recruiter Screen and the QA
  gate hold no ATS grant and read ATS facts from the pack. The grounding matrix
  no longer permits candidate-record reads for rediscovery; rediscovery is a
  count.
- Agents can actually open the connector runtime file (their brief no longer
  claims to be the only file they may read), and no agent is pointed at a wiki
  or document store it cannot reach; that material is read at intake and filed
  where agents look.
- Honest wording: scripts run as ordinary commands in Claude Code and in
  Cowork's sandbox only there; the ATS servers are not read-only by
  construction; Exa's search tools can return profile pages if asked with its
  people category, which agents are told never to do. Cowork adds a plugin's
  connectors from the plugin's Connectors tab, not at install; the agent tool
  entries need Claude Code 2.1.300 or later. Greenhouse, Ashby, Workday and
  Lever statements match the vendors' pages as of 2026-10-23.
- Renderer: a repeat row that is not an object fails up front with the row
  named instead of a traceback; a shape error removes a stale `.failed`
  attempt. Relay receives the working folder as an absolute path from every
  spawn. Setup no longer mentions Tavily, and `(none yet)` files nothing.

Changed

- The context budget counts the agent listing a session really holds
  (description plus tools line). Re-baselined: 1.0.3 2,806; 1.1.2 2,296;
  1.1.3 2,578 resident tokens.

Not exercised

- No live connector call was possible from the verification sandbox; the
  OAuth flows and tool grants are confirmed from vendor and Claude Code
  documentation and the Claude Code binary, not from an observed call. The
  acceptance gate and `claude plugin validate --strict` pass on this tree.

SHA-256 of `talent-one-1.1.3.plugin`: see docs/INSTALL.md and the `.sha256`
file beside the build in `dist/`.
