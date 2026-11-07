#!/bin/bash
# live_repeat.sh N - repeats the act test with the beacon at different offsets from container start
cd "$(dirname "$0")/.."
N=${1:-8}
OFFS=(31 33 35 37 39 41 43 45 47 49)
sudo -v
docker network create zt-net > /dev/null 2>&1
JIT='while true; do wget -q -O /dev/null http://zt-py:8000/$RANDOM; sleep $(( (RANDOM % 3) + 1 )); if [ $((RANDOM % 4)) -eq 0 ]; then wget -q -O /dev/null http://zt-py:8000/; fi; done'
echo "run offset_s phase_s frozen latency_s pclient_flagged"
for ((r = 0; r < N; r++)); do
  X=${OFFS[$r]}
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo rm -f /tmp/zt_live.jsonl /tmp/zt_ctl.txt
  sudo setsid ./build/loader -q -c -j /tmp/zt_live.jsonl > /dev/null 2>&1 < /dev/null &
  sleep 2
  sudo chmod a+r /tmp/zt_live.jsonl
  sudo setsid .venv/bin/python ml/controller.py /tmp/zt_live.jsonl --act --seconds 100 > /tmp/zt_ctl.txt 2>&1 < /dev/null &
  docker run -d --name zt-py --network zt-net python:alpine python -m http.server 8000 > /dev/null
  sleep 3
  docker run -d --name zt-pclient --network zt-net python:alpine sh -c "$JIT" > /dev/null
  sleep $((X - 3))
  T0=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_MONOTONIC))")
  for i in 1 2 3 4 5 6; do timeout 5 docker exec zt-py wget -q -T 1 -O /dev/null http://1.1.1.1:8443/ > /dev/null 2>&1; sleep 1; done
  for i in $(seq 25); do grep -q "FROZEN zt-py" /tmp/zt_ctl.txt && break; sleep 1; done
  F=$(grep -o 'FROZEN zt-py.*ts_ns=[0-9]*' /tmp/zt_ctl.txt | grep -o 'ts_ns=[0-9]*' | cut -d= -f2)
  PF=$(grep 'flagged=1' /tmp/zt_ctl.txt | grep -c zt-pclient)
  if [ -n "$F" ]; then
    L=$(python3 -c "print('%.2f' % (($F - $T0) / 1e9))"); S=yes
  else
    L=none; S=no
  fi
  echo "$((r + 1)) $X $((X % 10)) $S $L $PF"
  for c in zt-py zt-pclient; do
    CID=$(docker inspect -f '{{.Id}}' $c 2> /dev/null)
    [ -n "$CID" ] && sudo sh -c "echo 0 > /sys/fs/cgroup/system.slice/docker-$CID.scope/cgroup.freeze" 2> /dev/null
  done
  docker rm -f zt-py zt-pclient > /dev/null 2>&1
  sudo pkill -f controller.py
  sudo pkill -INT -x loader
  sleep 3
done
echo "REPEAT DONE"
