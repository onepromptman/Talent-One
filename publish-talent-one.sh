#!/usr/bin/env bash
# publish-talent-one.sh: create the GitHub release for an existing Talent One repo.
#
#   Prereqs:  gh auth login   (once, ever)
#   Run from the repo root (the folder holding .claude-plugin/):
#
#       bash publish-talent-one.sh [version]     # default: version in plugin.json
#
set -euo pipefail

OWNER="onepromptman"
REPO="Talent-One"

echo "==> preflight"
command -v gh >/dev/null || { echo "gh CLI not installed: https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "run: gh auth login"; exit 1; }
[ -f ".claude-plugin/plugin.json" ] || { echo "run this from the repo root"; exit 1; }

VERSION="${1:-$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')}"
TAG="v$VERSION"
PLUGIN="dist/talent-one-$VERSION.plugin"
NOTES="docs/RELEASE_NOTES_$VERSION.md"
for f in "$PLUGIN" "$PLUGIN.sha256" "$NOTES"; do [ -f "$f" ] || { echo "missing: $f"; exit 1; }; done
echo "    releasing $TAG"

echo "==> verifying build integrity"
WANT=$(cut -d' ' -f1 "$PLUGIN.sha256")
if command -v sha256sum >/dev/null; then GOT=$(sha256sum "$PLUGIN" | cut -d' ' -f1)
else GOT=$(shasum -a 256 "$PLUGIN" | cut -d' ' -f1); fi
[ "$GOT" = "$WANT" ] || { echo "SHA MISMATCH: expected $WANT, got $GOT"; exit 1; }
echo "    ok: $GOT"

echo "==> release $TAG"
gh release create "$TAG" "$PLUGIN" "$PLUGIN.sha256" \
  --repo "$OWNER/$REPO" \
  --title "Talent One $TAG" \
  --notes-file "$NOTES" \
  --latest

echo "DONE  ->  https://github.com/$OWNER/$REPO/releases/tag/$TAG"
