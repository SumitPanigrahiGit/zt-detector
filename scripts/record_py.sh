#!/bin/bash
# record_py.sh - python http.server plus a client; no baseline exists for this image
cd "$(dirname "$0")/.."
sudo -v
docker network create zt-net > /dev/null 2>&1
for r in 1 2; do
  OUT=data/py_$r.jsonl
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
  sleep 2
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 3
  docker run -d --name zt-pclient --network zt-net python:alpine sh -c 'while true; do wget -q -O /dev/null http://zt-py:8000/; sleep 1; done' > /dev/null
  sleep 70
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r "$OUT"
  echo "recorded $OUT: $(wc -l < "$OUT") events"
done
echo "PY DONE"
