#!/bin/bash
# record_pre.sh KIND REP - containers are already running when the loader starts
cd "$(dirname "$0")/.."
KIND=$1; REP=$2
OUT=data/pre_${KIND}_${REP}.jsonl
docker rm -f zt-victim zt-backend zt-proxy > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1
sudo rm -f "$OUT"
if [ "$KIND" = norm ]; then
  docker run -d --name zt-backend --network zt-net nginx:alpine > /dev/null
  docker run -d --name zt-proxy --network zt-net -v "$PWD/scripts/proxy.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine > /dev/null
else
  docker run -d --name zt-victim --network zt-net --cap-add SYS_PTRACE nginx:alpine > /dev/null
fi
sleep 15
sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
sleep 3
if [ "$KIND" = norm ]; then
  IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "zt-net").IPAddress}}' zt-proxy)
  END=$((SECONDS + 60)); i=0
  while [ $SECONDS -lt $END ]; do
    curl -s -m 2 -o /dev/null "http://$IP/"
    i=$((i + 1))
    [ $((i % 40)) -eq 0 ] && docker exec zt-proxy wget -q -T 2 -O /dev/null http://127.0.0.1/
    sleep 0.$((RANDOM % 5))
  done
else
  for i in $(seq 40); do docker exec zt-victim wget -q -T 1 -O /dev/null http://127.0.0.1/ 2>/dev/null; done
fi
sleep 2
docker rm -f zt-victim zt-backend zt-proxy > /dev/null 2>&1
sudo pkill -INT -x loader; sleep 2
sudo chmod a+r "$OUT"
echo "recorded $OUT: $(wc -l < "$OUT") events"
