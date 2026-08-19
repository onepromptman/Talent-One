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

1. Download [`dist/talent-one-1.0.3.plugin`](../dist/talent-one-1.0.3.plugin), or the file attached to the [latest release](../../../releases/latest).
2. Add it as a plugin from the plugin browser.

## Verify the download

```bash
sha256sum talent-one-1.0.3.plugin
# ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b
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

## Uninstall

```
/plugin uninstall talent-one@onepromptman
/plugin marketplace remove onepromptman
```
