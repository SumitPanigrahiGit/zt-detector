#!/bin/bash
# smoke_test.sh - checks host events, container events and container names
cd "$(dirname "$0")/.."
OUT=/tmp/zt_smoke.txt
rm -f "$OUT"
docker rm -f zt-smoke >/dev/null 2>&1

sudo timeout -s INT 10 ./build/loader > "$OUT" &
sleep 2

# Host events
whoami > /dev/null
hostname > /dev/null
date > /dev/null

# Container events
docker run -d --name zt-smoke alpine sleep 30 > /dev/null
sleep 1
docker exec zt-smoke whoami > /dev/null
docker exec zt-smoke hostname > /dev/null

wait
docker rm -f zt-smoke > /dev/null 2>&1

FAILED=0
for cmd in whoami hostname date; do
  if grep -q "$cmd" "$OUT"; then echo "PASS: host saw $cmd"
  else echo "FAIL: host missing $cmd"; FAILED=1; fi
done

if awk '$1=="EXEC" && $8 ~ /whoami$/ && $5!="host" && $6=="zt-smoke"' "$OUT" | grep -q .; then
  echo "PASS: container exec attributed to zt-smoke"
else
  echo "FAIL: no container row for zt-smoke"; FAILED=1
fi

if awk '$5=="host" && $6!="-"' "$OUT" | grep -q .; then
  echo "FAIL: container row labelled host"; FAILED=1
else
  echo "PASS: no container row mislabelled as host"
fi

[ "$FAILED" -eq 0 ] && echo "ALL TESTS PASSED" || exit 1
