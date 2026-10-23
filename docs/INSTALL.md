# Install

Talent One runs in **Cowork** (the Claude desktop app) and **Claude Code** (the command line).

It does **not** run in the regular Claude chat window. Chat cannot run the kit's eleven specialists, so `set up talent one` silently does nothing there. If nothing happens, you are in the wrong surface.

---

## Claude Code

```
/plugin marketplace add onepromptman/talent-one
/plugin install talent-one@onepromptman
```

Non-interactive equivalent:

```bash
claude plugin marketplace add onepromptman/talent-one
claude plugin install talent-one@onepromptman --scope user
```

## Cowork (Claude desktop app)

Open the plugin browser and add the marketplace `onepromptman/talent-one`, then install **Talent One**.

If your build of Cowork does not expose a marketplace field, use the direct build instead:

1. Download [`dist/talent-one-1.1.3.plugin`](../dist/talent-one-1.1.3.plugin), or the file attached to the [latest release](../../../releases/latest).
2. Add it as a plugin from the plugin browser.

## Verify the download

```bash
sha256sum talent-one-1.1.3.plugin
```

Compare with the row for your version.

| Build | SHA-256 |
| --- | --- |
| `talent-one-1.1.2.plugin` | `663c0e9612612afcd31c547b5e4db557cc1f5ae4565b2479e1457bbef84fb91b` |
| `talent-one-1.1.1.plugin` | `4014d3f2a4e4f28232157081559eaef97fa1db1edbdde6f55b7e2530d259a3ce` |
| `talent-one-1.1.0.plugin` | `d8ec24e499a8e4d589c46a04fbd1c050cae22080290cea861272fb3b2e298e93` |
| `talent-one-1.0.3.plugin` | `ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b` |

Each build also ships with a `.sha256` file beside it in `dist/`; that file is the authoritative hash for that build.

Older builds stay in `dist/`; none is ever overwritten.

The `.plugin` file is a zip. Rename it to `.zip` and look inside if you want to read every prompt before installing: it is all plain text.

---

## First run

```
set up talent one
```

A few questions about your company. Every one has a default and a skip. About five minutes, once.

Then:

```
Run Talent One for a Senior ML Engineer
```

or ask for any single artifact:

```
Write me a JD for a staff accountant
Build a talent map for a mechanical engineer in Denver
Make an interview plan for a security engineer
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
/plugin uninstall talent-one@onepromptman
/plugin marketplace remove onepromptman
```

In Cowork, open the plugin browser and remove **Talent One**.
