#!/bin/bash
# record_py4.sh - 2 jittered validation runs (100 s) and 2 poisoned learning runs (190 s)
cd "$(dirname "$0")/.."
sudo -v
docker network create zt-net > /dev/null 2>&1
JIT='while true; do wget -q -O /dev/null http://zt-py:8000/$RANDOM; sleep $(( (RANDOM % 3) + 1 )); if [ $((RANDOM % 4)) -eq 0 ]; then wget -q -O /dev/null http://zt-py:8000/; fi; done'
CLEAN='while true; do wget -q -O /dev/null http://zt-py:8000/; sleep 1; done'
rec() {   # name seconds client poison
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo setsid ./build/loader -q -c -j data/$1.jsonl > /dev/null 2>&1 < /dev/null &
  sleep 2
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 3
  docker run -d --name zt-pclient --network zt-net python:alpine sh -c "$3" > /dev/null
  if [ "$4" = poison ]; then
    sleep 20
    for i in 1 2 3 4 5 6 7 8 9 10 11 12; do docker exec zt-py wget -q -T 1 -O /dev/null http://1.1.1.1:8443/ 2>/dev/null; sleep 5; done
    sleep $(( $2 - 85 ))
  else
    sleep "$2"
  fi
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r data/$1.jsonl
  echo "recorded $1: $(wc -l < data/$1.jsonl) events"
}
rec pyj_1 100 "$JIT" no
rec pyj_2 100 "$JIT" no
rec pyp_1 190 "$CLEAN" poison
rec pyp_2 190 "$CLEAN" poison
echo "PY4 DONE"
