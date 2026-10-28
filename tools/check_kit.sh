#!/usr/bin/env bash
# Run the fill-contract linter (tools/check_fill.py) over a rendered run folder, or over
# the shipped templates.
#
#   tools/check_kit.sh                       # lint the shipped templates (TK_*.dc.html)
#   tools/check_kit.sh <run folder>          # lint a rendered run (<NN>_<agent>.html)
#
# A rendered artifact is linted against the template it was rendered from (matched by its
# artifact number, 03_atlas.html -> TK_03_*.dc.html) and against the run's compat
# handoffs.json when one sits in the folder. Works on the bash 3.2 that macOS ships.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
module="$(cd "$here/.." && pwd)"
tpl="$module/skills/talent-one/references/templates"
py="${PYTHON:-python3}"
dir="${1:-$tpl}"
fail=0
count=0

if [ "$dir" = "$tpl" ]; then
  pattern='TK_*.dc.html'
else
  pattern='[0-9][0-9]_*.html'
fi

for f in "$dir"/$pattern; do
  [ -e "$f" ] || continue
  base="$(basename "$f")"
  # The per-file flags live in the positional parameters, not an array: under `set -u`,
  # bash 3.2 treats "${arr[@]}" of an EMPTY array as an unbound variable and aborts,
  # while "$@" with no parameters is always safe.
  set --
  if [ "$dir" != "$tpl" ]; then
    nn="${base%%_*}"
    match="$(ls "$tpl"/TK_"$nn"_*.dc.html 2>/dev/null | head -1)"
    [ -n "$match" ] && set -- "$@" --template "$match"
    [ -f "$dir/handoffs.json" ] && set -- "$@" --handoffs "$dir/handoffs.json" --artifact "$nn"
  fi
  case "$base" in TK_00_*) set -- "$@" --reference ;; esac

  printf '\n=== %s\n' "$base"
  count=$((count + 1))
  "$py" "$here/check_fill.py" "$f" "$@" --quiet || fail=1
done

echo
if [ "$count" -eq 0 ]; then
  echo "fill contract: no artifacts found in $dir"
  exit 2
elif [ "$fail" -eq 0 ]; then
  echo "fill contract: clean ($count file(s))"
else
  echo "fill contract: FAILURES above ($count file(s))"
fi
exit "$fail"
