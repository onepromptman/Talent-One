#!/usr/bin/env bash
# publish-talent-one.sh — create the GitHub repo and ship 1.0.3, start to finish.
#
#   Prereqs:  gh auth login   (once, ever)
#   Run from INSIDE the unzipped talent-one/ folder:
#
#       bash publish-talent-one.sh
#
set -euo pipefail

OWNER="onepromptman"
REPO="talent-one"
TAG="v1.0.3"
PLUGIN="dist/talent-one-1.0.3.plugin"
SHA="ca7f3c207ab89cce313b6c5c47b92aaeee45794e402aeac74eb2823e934ab88b"

echo "==> preflight"
command -v gh >/dev/null || { echo "gh CLI not installed: https://cli.github.com"; exit 1; }
gh auth status >/dev/null || { echo "run: gh auth login"; exit 1; }
[ -f ".claude-plugin/plugin.json" ] || { echo "run this from inside the talent-one/ folder"; exit 1; }

echo "==> verifying build integrity"
if command -v sha256sum >/dev/null; then GOT=$(sha256sum "$PLUGIN" | cut -d' ' -f1)
else GOT=$(shasum -a 256 "$PLUGIN" | cut -d' ' -f1); fi
[ "$GOT" = "$SHA" ] || { echo "SHA MISMATCH — expected $SHA, got $GOT"; exit 1; }
echo "    ok: $GOT"

echo "==> git init + first commit"
git init -q 2>/dev/null || true
git add -A
git -c user.name="Onepromptman" commit -qm "Talent One 1.0.3 — eleven-agent hiring package kit" || echo "    (nothing to commit)"
git branch -M main

echo "==> creating github.com/$OWNER/$REPO"
gh repo create "$OWNER/$REPO" \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Eleven coordinated talent-acquisition agents. One role brief in, a full eight-document hiring package out. Runs in Claude Code and Cowork." \
  --homepage "https://github.com/$OWNER/$REPO"

echo "==> topics"
gh repo edit "$OWNER/$REPO" \
  --add-topic claude-code --add-topic claude-plugin --add-topic cowork \
  --add-topic recruiting --add-topic talent-acquisition --add-topic hiring \
  --add-topic sourcing --add-topic ai-agents

echo "==> release $TAG"
gh release create "$TAG" "$PLUGIN" \
  --repo "$OWNER/$REPO" \
  --title "Talent One $TAG" \
  --notes-file docs/RELEASE_NOTES_1.0.3.md \
  --latest

echo
echo "DONE  ->  https://github.com/$OWNER/$REPO"
echo
echo "Install line to share:"
echo "    /plugin marketplace add $OWNER/$REPO"
echo "    /plugin install talent-one@$OWNER"
