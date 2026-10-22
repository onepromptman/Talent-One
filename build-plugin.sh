#!/usr/bin/env bash
# build-plugin.sh: package the plugin source into dist/talent-one-<version>.plugin
# (a zip) and write its sha256 beside it. Never overwrites an existing build:
# every version stays as its own file.
#
#   bash build-plugin.sh            # version read from .claude-plugin/plugin.json
#   bash build-plugin.sh 1.1.2      # explicit version (must match plugin.json)
set -euo pipefail
cd "$(dirname "$0")"
[ -f .claude-plugin/plugin.json ] || { echo "run from the repo root"; exit 1; }
PJ=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")
V=${1:-$PJ}
[ "$V" = "$PJ" ] || { echo "version $V does not match plugin.json ($PJ)"; exit 1; }
OUT="dist/talent-one-$V.plugin"
[ -e "$OUT" ] && { echo "$OUT already exists; bump the version instead of overwriting"; exit 1; }
[ -f "docs/RELEASE_NOTES_$V.md" ] || { echo "docs/RELEASE_NOTES_$V.md is missing"; exit 1; }
# What ships: plugin manifest, bundled connector list, the eleven agents, the
# skills with their references and scripts, and the user-facing docs. Only
# committed files ship: a dirty tree (edits or untracked files under these
# paths) is refused, so the build is exactly what HEAD holds.
SHIP=(agents skills .claude-plugin .mcp.json README.md LICENSE.md CONNECTORS.md
      CHANGELOG.md docs/INSTALL.md "docs/RELEASE_NOTES_$V.md")
DIRTY=$(git status --porcelain -- "${SHIP[@]}")
[ -z "$DIRTY" ] || { echo "uncommitted changes in shipped paths; commit or stash first:"; echo "$DIRTY"; exit 1; }
mkdir -p dist
git ls-files -z -- "${SHIP[@]}" | xargs -0 zip -q -X "$OUT"
( cd dist && sha256sum "talent-one-$V.plugin" > "talent-one-$V.plugin.sha256" )
echo "built $OUT ($(unzip -Z1 "$OUT" | wc -l) files)"
cat "dist/talent-one-$V.plugin.sha256"
