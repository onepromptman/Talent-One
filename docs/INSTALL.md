# Install

Talent One runs in **Cowork** (the Claude desktop app) and **Claude Code** (the command line).

Use a writable folder and Python 3.10 or later in the plugin's working environment.
Nothing else needs installing: the renderer's one package ships inside the plugin.

---

## Claude Code

```
/plugin marketplace add onepromptman/Talent-One
/plugin install talent-one@talent-one
```

Non-interactive equivalent:

```bash
claude plugin marketplace add onepromptman/Talent-One
claude plugin install talent-one@talent-one --scope user
```

Upgrading from Talent One 1.x: 1.x was installed from this repository under a
marketplace named `onepromptman`, and 2.x starts a fresh history under a marketplace
named `talent-one`. Remove the old one first, then add this one as above:

```
/plugin uninstall talent-one@onepromptman
/plugin marketplace remove onepromptman
```

## Cowork (Claude desktop app)

Open the plugin browser and add the marketplace `onepromptman/Talent-One`, then install **Talent One**.

---

## First run

```
set up talent one
```

Five questions about your company. Every one has a default and a skip. About five minutes, once, and less if another OnePromptMan kit already ran setup: the profile is shared (`onepromptman-profile.md`).

Then:

```
Run Talent One for a Senior ML Engineer
```

or ask for any single artifact:

```
Write me a JD for a staff accountant
Build a talent map for a mechanical engineer in Denver
Make an interview plan for a security engineer
Coach my interviewers for a security engineer loop
```

## Connectors (optional)

Four remote connectors ship with the plugin: Exa, Bright Data, Greenhouse, Ashby. Nothing is required; the kit runs fully on public data, and nothing is sent to any of them until you sign in.

- Claude Code (2.1.300 or later for the agents to see them): the four servers register when the plugin is enabled; sign in to the ones you want from `/mcp`.
- Cowork: installing the plugin does not add them. Open the plugin's Connectors tab, add each one you want, then sign in. On Team and Enterprise plans an Owner adds connectors for the organization.
- Greenhouse: a Site Admin connects first and sets scopes under Dev Center, MCP Access (keep write scopes off, deselect Candidates and Attachments at consent). Ashby: an Org Admin turns on the MCP Server opt-in and connecting users need Elevated Access. Exa and Bright Data: a free account on each is enough. No API key is stored in the plugin.

Switch off any you do not use in `/mcp`. Details and the privacy rules: [CONNECTORS.md](../CONNECTORS.md).

## Uninstall

In Claude Code:

```
/plugin uninstall talent-one@talent-one
/plugin marketplace remove talent-one
```

In Cowork, open the plugin browser and remove **Talent One**.
