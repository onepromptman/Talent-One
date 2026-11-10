#!/usr/bin/env bash
# Talent One acceptance gate. Run from the repository root: bash evals/run_gate.sh
# Uses only the kit's own worked examples. Exits nonzero on any failure.
cd "$(dirname "$0")/.." || exit 1
PY="${PYTHON:-python3}"
SK=$PWD/skills/talent-one; R=$SK/scripts/render.py; REF=$SK/references
OUT=$PWD/evals/out; mkdir -p "$OUT"; FAILS=0
step() { if [ "$2" = 0 ]; then echo "PASS  $1"; else echo "FAIL  $1"; FAILS=$((FAILS+1)); fi; }

(cd "$SK" && "$PY" scripts/build_briefs.py --check) >"$OUT/briefs.log" 2>&1; step "build_briefs --check" $?
"$PY" "$SK/scripts/context_budget.py" --check >"$OUT/budget.log" 2>&1; step "context_budget --check" $?

bad=0
for T in "$REF"/templates/TK_0[1-9]_*.dc.html; do
  "$PY" "$R" lint-template --template "$T" >"$OUT/lint.json" 2>/dev/null \
    && grep -q '"verdict": "CLEAN"' "$OUT/lint.json" \
    || { bad=$((bad+1)); echo "      lint not clean: $(basename "$T")"; }
done
step "lint-template x9 CLEAN" $bad

DS=$(ls -d "$REF"/templates/_ds/*/ | head -1); bad=0; med=0; low=0
for N in 01 02 03 04 05 06 07 08 09; do
  T=$(ls "$REF"/templates/TK_${N}_*.dc.html); H="$OUT/TK_$N.html"
  SCH="$REF/content-schemas/TK_$N.content-schema.json"; CON="$REF/content-schemas/TK_$N.example-content.json"
  "$PY" "$R" render --template "$T" --schema "$SCH" --content "$CON" --ds "$DS" --out "$H" \
    --strict --mode light --prefix TK --credit on >"$OUT/TK_$N.render.log" 2>&1 \
    || { bad=$((bad+1)); echo "      render error: TK_$N (see evals/out/TK_$N.render.log)"; continue; }
  "$PY" "$R" verify --template "$T" --schema "$SCH" --doc "$H" --content "$CON" \
    >"$OUT/TK_$N.verify.json" 2>"$OUT/TK_$N.verify.log"
  status=$?
  c=$("$PY" -c '
import json, sys
# Rendering the worked example and verifying it against itself trips two checks by construction.
SELF = ("surviving example text", "identical to example")
f = json.load(open(sys.argv[1], encoding="utf-8"))["findings"]
if int(sys.argv[2]) != int(any(x["severity"] == "HIGH" for x in f)):
    sys.exit("verifier exit status disagrees with its findings")
own = [x for x in f if not x.get("check", "").startswith(SELF)]
n = lambda s: sum(1 for x in own if x.get("severity") == s)
print(n("HIGH"), n("MEDIUM"), n("LOW"))
' "$OUT/TK_$N.verify.json" "$status") || { bad=$((bad+1)); echo "      verify error: TK_$N"; continue; }
  read -r h m l <<<"$c"
  [ "$h" -gt 0 ] && { bad=$((bad+1)); echo "      HIGH findings: TK_$N ($h)"; }
  med=$((med+m)); low=$((low+l))
done
step "render + verify examples x9 (0 HIGH required; MEDIUM $med, LOW $low, self-match checks excluded)" $bad

bad=0
if grep -rIn --exclude-dir=_ds --exclude='*.py' $'\xe2\x80\x94' agents skills README.md CHANGELOG.md CONNECTORS.md docs/*.md >"$OUT/emdash.log" 2>/dev/null; then
  bad=1; echo "      em dashes found (see evals/out/emdash.log)"; fi
# In a git checkout, check the tracked files. Anywhere else (an unpacked zip, an installed
# plugin) there is no index to ask, so check every file on disk instead of passing blind.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  FILES=$(git ls-files .); KIND=tracked
else
  echo "      not a git checkout: checking every file in this folder instead of tracked files"
  FILES=$(find . -type f -not -path './evals/out/*' -not -path './.git/*' -not -path './.venv/*'     -not -path '*/__pycache__/*' -not -path './.pytest_cache/*' | sed 's|^\./||'); KIND=shipped
fi
TRACKED=$(printf '%s
' "$FILES" | grep -E '(^|/)(talent-one-roles|talent-one-runs|talent-one-kb|runs|roles|\.claude)/|(talent-one|onepromptman)-profile\.md$|\.content\.json$' | grep -v '^skills/talent-one/references/content-schemas/')
[ -n "$TRACKED" ] && { bad=1; echo "      $KIND run/profile/content files:"; echo "$TRACKED"; }
step "repo hygiene (no em dashes, no tracked run files)" $bad

echo; [ "$FAILS" = 0 ] && echo "GATE PASS" || echo "GATE FAIL ($FAILS step(s))"
[ "$FAILS" = 0 ]
