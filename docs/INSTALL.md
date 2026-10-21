# Install

Talent One runs in **Claude Code** (CLI) and **Cowork** (the Claude desktop app).

It does **not** run in the regular Claude chat window. Chat cannot spawn the kit's eleven sub-agents, so `set up talent one` silently does nothing there. If nothing happens, you are in the wrong surface.

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

1. Download [`dist/talent-one-1.1.0.plugin`](../dist/talent-one-1.1.0.plugin), or the file attached to the [latest release](../../../releases/latest).
2. Add it as a plugin from the plugin browser.

## Verify the download

```bash
sha256sum talent-one-1.1.0.plugin
# 04c5001730a0ef780af06ead1eb14685ecd2c5cbf98ca241c8ec2254bb2c348b
```

The `.plugin` file is a zip. Rename it to `.zip` and look inside if you want to read every prompt before installing — it is all plain text.

---

## First run

```
set up talent one
```

Five questions about your company. Every one has a default and a skip. About five minutes, once.

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

Four remote connectors ship with the plugin: Exa, Bright Data, Greenhouse, Ashby. Nothing is required; the kit runs fully on public data.

- Exa works at once, keyless. Sign in from `/mcp` (Claude Code) or the plugin's Connectors tab (Cowork) to use your own plan.
- Bright Data, Greenhouse, and Ashby sign in with OAuth from `/mcp` (Claude Code) or the plugin's Connectors tab (Cowork); for the two ATS servers your admin enables MCP access on the vendor side first. No API key is stored in the plugin.

Switch off any you do not use in `/mcp`. Details and the privacy rules: [CONNECTORS.md](../CONNECTORS.md).

## Uninstall

```
/plugin uninstall talent-one@onepromptman
/plugin marketplace remove onepromptman
```
