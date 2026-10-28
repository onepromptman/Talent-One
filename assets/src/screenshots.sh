#!/usr/bin/env bash
# Rebuild the README images with headless Chrome: assets/hero.png from assets/src/hero.html,
# and assets/samples/NN.png (the first screen of each samples/NN_*_SAMPLE.html).
# Run from the repository root. CHROME overrides the browser binary.
set -euo pipefail
cd "$(dirname "$0")/../.."
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
PROFILE=$(mktemp -d); trap 'rm -rf "$PROFILE"' EXIT
shot() { "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run \
  --user-data-dir="$PROFILE" --force-device-scale-factor=2 --window-size="$3" \
  --screenshot="$2" "file://$PWD/$1" >/dev/null 2>&1; echo "wrote $2"; }
shot assets/src/hero.html assets/hero.png 1320,930
for f in samples/0[1-9]_*_SAMPLE.html; do
  n=$(basename "$f" | cut -c1-2)
  shot "$f" "assets/samples/$n.png" 1280,900
done
