#!/bin/bash
# record_py2.sh - python image: 3 learning runs (190 s), 2 validation runs (100 s), attacks (beacon, burst x3)
cd "$(dirname "$0")/.."
sudo -v
docker network create zt-net > /dev/null 2>&1
CLIENT='while true; do wget -q -O /dev/null http://zt-py:8000/; sleep 1; done'
run_normal() {   # name seconds
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo setsid ./build/loader -q -c -j data/$1.jsonl > /dev/null 2>&1 < /dev/null &
  sleep 2
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 3
  docker run -d --name zt-pclient --network zt-net python:alpine sh -c "$CLIENT" > /dev/null
  sleep "$2"
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r data/$1.jsonl
  echo "recorded $1: $(wc -l < data/$1.jsonl) events"
}
run_attack() {   # kind rep
  OUT=data/pya_$1_$2.jsonl
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
  sleep 2
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 12
  case $1 in
    beacon) for i in 1 2 3 4 5 6; do docker exec zt-py wget -q -T 1 -O /dev/null http://1.1.1.1:8443/ 2>/dev/null; sleep 1; done ;;
    burst)  for i in $(seq 40); do docker exec zt-py wget -q -T 1 -O /dev/null http://127.0.0.1:8000/ 2>/dev/null; done ;;
  esac
  sleep 2
  docker rm -f zt-py > /dev/null 2>&1
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r "$OUT"
  echo "recorded $OUT: $(wc -l < "$OUT") events"
}
for r in 1 2 3; do run_normal pyl_$r 190; done
for r in 1 2; do run_normal pyv_$r 100; done
for k in beacon burst; do for r in 1 2 3; do run_attack $k $r; done; done
echo "PY2 DONE"
