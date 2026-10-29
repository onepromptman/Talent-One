#!/usr/bin/env bash
# build-plugin.sh: package this plugin as dist/talent-one-<version>.plugin
# (a zip) and write its sha256 beside it. Never overwrites an existing build: every version
# stays its own file. Only committed files ship: a dirty tree (edits or untracked files under
# the shipped paths) is refused, so the build is exactly what HEAD holds.
#
#   bash build-plugin.sh            # version read from .claude-plugin/plugin.json
#   bash build-plugin.sh 2.1.0      # explicit version (must match plugin.json)
#
# The marketplace install (`/plugin install talent-one@talent-one`) needs none of this; the
# .plugin file is for surfaces that take a plugin upload instead of a marketplace.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .claude-plugin/plugin.json ] || { echo "run from the plugin root"; exit 1; }
PJ=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")
V=${1:-$PJ}
[ "$V" = "$PJ" ] || { echo "version $V does not match plugin.json ($PJ)"; exit 1; }
OUT="dist/talent-one-$V.plugin"
[ -e "$OUT" ] && { echo "$OUT already exists; bump the version instead of overwriting"; exit 1; }
grep -qE "^## \[?${V//./\\.}\]?( |$)" CHANGELOG.md || { echo "CHANGELOG.md has no '## $V' (or '## [$V]') entry"; exit 1; }
# What ships: plugin manifest, bundled connector list, the agents, the skills with their
# references and scripts, and the user-facing docs.
SHIP="agents skills .claude-plugin .mcp.json README.md CONNECTORS.md CHANGELOG.md docs/INSTALL.md"
# shellcheck disable=SC2086
DIRTY=$(git status --porcelain -- $SHIP)
[ -z "$DIRTY" ] || { echo "uncommitted changes in shipped paths; commit or stash first:"; echo "$DIRTY"; exit 1; }
STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"' EXIT
# shellcheck disable=SC2086
git archive HEAD -- $SHIP | tar -x -C "$STAGE"
# the license lives at the repository root; ship a copy inside the plugin
ROOT=$(git rev-parse --show-toplevel)
if [ -f LICENSE ]; then git show HEAD:"$(git rev-parse --show-prefix)LICENSE" > "$STAGE/LICENSE"
elif [ -f "$ROOT/LICENSE" ]; then git -C "$ROOT" show HEAD:LICENSE > "$STAGE/LICENSE"; fi
# the copied license gets the commit's time like every archived file, so rebuilds are byte-identical
STAMP=$(TZ=UTC git log -1 --format=%cd --date=format-local:%Y%m%d%H%M.%S)
find "$STAGE" -maxdepth 1 -name 'LICENSE*' -exec env TZ=UTC touch -t "$STAMP" {} +
mkdir -p dist
( cd "$STAGE" && find . -type f | LC_ALL=C sort | sed 's|^\./||' | zip -q -X -@ "$OLDPWD/$OUT" )
if command -v sha256sum >/dev/null; then SUM="sha256sum"; else SUM="shasum -a 256"; fi
( cd dist && $SUM "talent-one-$V.plugin" > "talent-one-$V.plugin.sha256" )
echo "built $OUT ($(unzip -Z1 "$OUT" | wc -l | tr -d ' ') files)"
cat "dist/talent-one-$V.plugin.sha256"
