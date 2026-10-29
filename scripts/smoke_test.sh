#!/bin/bash
# smoke_test.sh - runs the loader for a few seconds and checks it saw known commands
cd "$(dirname "$0")/.."
OUT=/tmp/zt_smoke.txt
rm -f "$OUT"

sudo timeout -s INT 6 ./build/loader > "$OUT" &
sleep 2

# Generate known exec events
whoami > /dev/null
hostname > /dev/null
date > /dev/null

wait

for cmd in whoami hostname date; do
  if grep -q "$cmd" "$OUT"; then
    echo "PASS: saw $cmd"
  else
    echo "FAIL: missing $cmd"
    FAILED=1
  fi
done

head -5 "$OUT"
[ -z "$FAILED" ] && echo "ALL TESTS PASSED" || exit 1
