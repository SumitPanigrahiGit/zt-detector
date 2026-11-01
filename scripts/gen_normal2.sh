#!/bin/bash
# gen_normal2.sh SECONDS - proxy + backend with varied, still-normal traffic
cd "$(dirname "$0")/.."
DUR=${1:-300}
docker rm -f zt-backend zt-proxy > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1
docker run -d --name zt-backend --network zt-net nginx:alpine > /dev/null
docker run -d --name zt-proxy --network zt-net \
  -v "$PWD/scripts/proxy.conf:/etc/nginx/conf.d/default.conf:ro" nginx:alpine > /dev/null
sleep 3
IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "zt-net").IPAddress}}' zt-proxy)
END=$((SECONDS + DUR)); i=0
while [ $SECONDS -lt $END ]; do
  case $((RANDOM % 5)) in
    0) curl -s -m 2 -o /dev/null "http://$IP/" ;;
    1) curl -s -m 2 -o /dev/null "http://$IP/missing-$RANDOM" ;;
    2) curl -s -m 2 -o /dev/null -X POST -d "a=$RANDOM" "http://$IP/" ;;
    3) for k in 1 2 3; do curl -s -m 2 -o /dev/null "http://$IP/" & done; wait ;;
    4) curl -s -m 2 -o /dev/null -H "User-Agent: probe-$RANDOM" "http://$IP/index.html" ;;
  esac
  i=$((i + 1))
  [ $((i % 40)) -eq 0 ] && docker exec zt-proxy wget -q -T 2 -O /dev/null http://127.0.0.1/
  [ $((i % 90)) -eq 0 ] && docker exec zt-proxy nginx -s reload > /dev/null 2>&1
  sleep 0.$((RANDOM % 5))
done
docker rm -f zt-backend zt-proxy > /dev/null 2>&1
