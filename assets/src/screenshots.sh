#!/usr/bin/env bash
# Rebuild the README images with headless Chrome: assets/hero.png from assets/src/hero.html,
# and assets/samples/NN.png (the first screen of each samples/NN_*_SAMPLE.html).
# Run from the repository root. CHROME overrides the browser binary.
# By default it is the first of the macOS and Windows install paths that exists.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${CHROME:-}" ]; then
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/c/Program Files/Google/Chrome/Application/chrome.exe" \
           "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"; do
    [ -x "$c" ] && { CHROME=$c; break; }
  done
fi
: "${CHROME:?no Chrome found; set CHROME=/path/to/chrome}"
# Paths handed to Chrome are absolute; under Git Bash on Windows they need a drive letter
# (C:/...), not /c/..., for the file:// URL, the output file and the profile directory.
PROFILE=$(mktemp -d); trap 'rm -rf "$PROFILE"' EXIT
ROOT=$PWD; PROFILE_W=$PROFILE
if command -v cygpath >/dev/null 2>&1; then
  ROOT=$(cygpath -m "$PWD"); PROFILE_W=$(cygpath -m "$PROFILE")
fi
shot() {
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run \
    --user-data-dir="$PROFILE_W" --force-device-scale-factor=2 --window-size="$3" \
    --screenshot="$ROOT/$2" "file://$ROOT/$1" >/dev/null 2>&1 || { echo "FAILED $2"; exit 1; }
  echo "wrote $2"
}
shot assets/src/hero.html assets/hero.png 1320,1184
for f in samples/0[1-9]_*_SAMPLE.html; do
  n=$(basename "$f" | cut -c1-2)
  shot "$f" "assets/samples/$n.png" 1280,900
done
