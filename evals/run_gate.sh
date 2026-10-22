#!/usr/bin/env bash
# Talent One acceptance gate. Run from the repo root: bash evals/run_gate.sh
# Uses only the kit's own worked examples. Exits nonzero on any failure.
cd "$(dirname "$0")/.." || exit 1
SK=$PWD/skills/talent-one; R=$SK/scripts/render.py; REF=$SK/references
OUT=$PWD/evals/out; mkdir -p "$OUT"; FAILS=0
step() { if [ "$2" = 0 ]; then echo "PASS  $1"; else echo "FAIL  $1"; FAILS=$((FAILS+1)); fi; }

(cd "$SK" && python3 scripts/build_briefs.py --check) >"$OUT/briefs.log" 2>&1; step "build_briefs --check" $?
python3 "$SK/scripts/context_budget.py" --check >"$OUT/budget.log" 2>&1; step "context_budget --check" $?

bad=0
for T in "$REF"/templates/TK_0[1-8]_*.dc.html; do
  python3 "$R" lint-template --template "$T" >"$OUT/lint.json" 2>/dev/null
  grep -q '"verdict": "CLEAN"' "$OUT/lint.json" || { bad=$((bad+1)); echo "      lint not clean: $(basename "$T")"; }
done
step "lint-template x8 CLEAN" $bad

FLAGS=""
if python3 "$R" render --help 2>&1 | grep -q -- --prefix; then FLAGS="--prefix TK --credit on"
else echo "WARN  renderer has no --prefix/--credit yet; rendering without them"; fi
DS=$(ls -d "$REF"/templates/_ds/*/ | head -1); bad=0; med=0; low=0
for N in 01 02 03 04 05 06 07 08; do
  T=$(ls "$REF"/templates/TK_${N}_*.dc.html); H="$OUT/TK_$N.html"
  SCH="$REF/content-schemas/TK_$N.content-schema.json"; CON="$REF/content-schemas/TK_$N.example-content.json"
  python3 "$R" render --template "$T" --schema "$SCH" --content "$CON" --ds "$DS" --out "$H" \
    --strict --mode light $FLAGS >"$OUT/TK_$N.render.log" 2>&1 \
    || { bad=$((bad+1)); echo "      render error: TK_$N (see evals/out/TK_$N.render.log)"; continue; }
  python3 "$R" verify --template "$T" --schema "$SCH" --doc "$H" --content "$CON" \
    --out "$OUT/TK_$N.verify.json" >/dev/null 2>&1
  c=$(python3 -c '
import json, sys
# Rendering the worked example and verifying it against itself trips two checks by construction.
SELF = ("surviving example text", "identical to example")
f = json.load(open(sys.argv[1])).get("findings", [])
own = [x for x in f if not x.get("check", "").startswith(SELF)]
n = lambda s: sum(1 for x in own if x.get("severity") == s)
print(n("HIGH"), n("MEDIUM"), n("LOW"))
' "$OUT/TK_$N.verify.json") || { bad=$((bad+1)); echo "      verify error: TK_$N"; continue; }
  read -r h m l <<<"$c"
  [ "$h" -gt 0 ] && { bad=$((bad+1)); echo "      HIGH findings: TK_$N ($h)"; }
  med=$((med+m)); low=$((low+l))
done
step "render + verify examples x8 (0 HIGH required; MEDIUM $med, LOW $low, self-match checks excluded)" $bad

bad=0
if grep -rIn --exclude-dir=_ds --exclude='*.py' $'\xe2\x80\x94' agents skills README.md CHANGELOG.md CONNECTORS.md docs/*.md >"$OUT/emdash.log" 2>/dev/null; then
  bad=1; echo "      em dashes found (see evals/out/emdash.log)"; fi
TRACKED=$(git ls-files | grep -E '(^|/)(runs|roles)/|talent-one-profile\.md$|\.content\.json$' | grep -v '^skills/talent-one/references/content-schemas/')
[ -n "$TRACKED" ] && { bad=1; echo "      tracked run/profile/content files:"; echo "$TRACKED"; }
step "repo hygiene (no em dashes, no tracked run files)" $bad

echo; [ "$FAILS" = 0 ] && echo "GATE PASS" || echo "GATE FAIL ($FAILS step(s))"
[ "$FAILS" = 0 ]
