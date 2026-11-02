#!/bin/bash
# record_py3.sh - fresh python attacks (reps 4 to 6), recorded after the threshold fix
cd "$(dirname "$0")/.."
sudo -v
docker network create zt-net > /dev/null 2>&1
for k in beacon burst; do for r in 4 5 6; do
  OUT=data/pya_${k}_$r.jsonl
  docker rm -f zt-py > /dev/null 2>&1
  sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
  sleep 2
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 12
  if [ "$k" = beacon ]; then
    for i in 1 2 3 4 5 6; do docker exec zt-py wget -q -T 1 -O /dev/null http://1.1.1.1:8443/ 2>/dev/null; sleep 1; done
  else
    for i in $(seq 40); do docker exec zt-py wget -q -T 1 -O /dev/null http://127.0.0.1:8000/ 2>/dev/null; done
  fi
  sleep 2
  docker rm -f zt-py > /dev/null 2>&1
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r "$OUT"
  echo "recorded $OUT: $(wc -l < "$OUT") events"
done; done
echo "PY3 DONE"
