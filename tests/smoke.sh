#!/usr/bin/env bash
# Smoke test of the factory against real GitHub, with the sandbox foreman `sandy` only.
# It takes the issue "Smoke test" of the sandbox through every stage and checks
# `factory status --json` and `factory audit` at each step. It ends in Done.
# Idempotent: it uses the same issue each run (it makes it on the first run) and resets it first.
#
# Run: tests/smoke.sh     (FACTORY=/path/to/factory to test another CLI; default: bin/factory of this repo)
set -euo pipefail

FOREMAN=sandy   # fixed: the smoke test writes human directives; never point it at a live board
TITLE="Smoke test"
SESSION=smoke-test
NOTE="smoke test"
F=${FACTORY:-"$(cd "$(dirname "$0")/.." && pwd)/bin/factory"}
unset FACTORY_FAKE

step() { printf '\n== %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
run() { echo "\$ factory $*"; "$F" "$@"; }
refused() {  # the command must be refused by a rule (exit code 1)
  echo "\$ factory $* (must be refused)"
  local code=0; "$F" "$@" || code=$?
  [ "$code" = 1 ] || fail "factory $* gave exit code $code, not 1"
}

# expect STAGE FLAGS NEXT: the issue in `factory status --json` and `factory audit` with no problems.
expect() {
  "$F" status "$FOREMAN" --json | python3 -c '
import json, sys
ref, stage, flags, action = sys.argv[1:]
st = json.load(sys.stdin)
issue = next((i for i in st["issues"] if i["id"] == ref), None)
if issue is None:
    sys.exit(f"{ref} is not in factory status")
got = (issue["stage"], ",".join(issue["flags"]) or "-", issue["next_action"] or "-")
if got != (stage, flags, action):
    sys.exit(f"{ref}: (stage, flags, next_action) is {got}, expected {(stage, flags, action)}")
print(f"ok: {ref} stage={stage} flags={flags} next_action={action}")
' "$REF" "$1" "$2" "$3" || fail "factory status"
  [ "$("$F" audit "$FOREMAN")" = "no problems" ] || fail "factory audit $FOREMAN"
  echo "ok: factory audit $FOREMAN: no problems"
}

REPO=$("$F" status "$FOREMAN" --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["github"])')

step "find or make the issue \"$TITLE\" in $REPO"
NUMBER=$(gh api --paginate "repos/$REPO/issues?state=all&per_page=100" | python3 -c '
import json, sys
dec, text, i, found = json.JSONDecoder(), sys.stdin.read(), 0, []
while i < len(text):
    if text[i].isspace():
        i += 1
        continue
    page, i = dec.raw_decode(text, i)
    found += [x["number"] for x in page if x["title"] == sys.argv[1] and "pull_request" not in x]
print(min(found) if found else "")
' "$TITLE")
if [ -z "$NUMBER" ]; then
  out=$(run new "$TITLE" --foreman "$FOREMAN" --body "Used by tests/smoke.sh of the factory repo. Do not use it for other work.")
  echo "$out"
  NUMBER=$(echo "$out" | sed -n 's/^[A-Z0-9]*-\([0-9]*\):.*/\1/p')
fi
REF=$("$F" resolve "$FOREMAN $NUMBER" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "issue: $REF"

step "reset: no flags, Backlog"
run release "$REF"
run unblock "$REF" --note "$NOTE"
run reworked "$REF"
run move "$REF" backlog --note "$NOTE"
expect backlog - -
refused advance "$REF"

step "Backlog -> In Design (human go), then agent advance"
run go "$REF" --note "$NOTE"
expect design - design
run claim "$REF" "$SESSION"
expect design claimed -
run advance "$REF" --session "$SESSION"
run release "$REF"
expect ready - -
refused advance "$REF"

step "Ready for Dev -> In Dev (human approve), block and unblock, then agent advance"
run approve "$REF" --note "$NOTE"
expect dev - develop
run claim "$REF" "$SESSION"
run block "$REF" "Smoke test question"
expect dev claimed,blocked -
run unblock "$REF" --note "$NOTE"
run advance "$REF" --session "$SESSION"
refused advance "$REF"
run release "$REF"
expect verify - -

step "Waiting for Verification: rework, then verified, then agent advance to Done"
run rework "$REF" "$NOTE"
expect verify rework rework
run reworked "$REF"
refused advance "$REF"
run verified "$REF" --note "$NOTE"
expect verify - ship
run advance "$REF" --session "$SESSION"

step "end state"
"$F" show "$REF" | python3 -c '
import json, sys
s = json.load(sys.stdin)
if (s["stage"], s["flags"]) != ("done", []):
    sys.exit("stage=%s flags=%s, expected done and no flags" % (s["stage"], s["flags"]))
' || fail "factory show $REF"
state=$(gh api "repos/$REPO/issues/$NUMBER" --jq .state)
[ "$state" = closed ] || fail "$REF is $state, expected closed"
"$F" status "$FOREMAN" --json | python3 -c '
import json, sys
open_ids = [i["id"] for i in json.load(sys.stdin)["issues"]]
sys.exit(f"{sys.argv[1]} is still in factory status" if sys.argv[1] in open_ids else 0)
' "$REF" || fail "factory status"
[ "$("$F" audit "$FOREMAN")" = "no problems" ] || fail "factory audit $FOREMAN"
echo "ok: $REF is in Done, closed, with no flags; factory audit $FOREMAN: no problems"
echo
echo "PASS: smoke test"
