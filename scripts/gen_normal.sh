#!/bin/bash
# gen_normal.sh - runs proxy + backend nginx and sends steady traffic
cd "$(dirname "$0")/.."
DUR=${1:-300}

docker rm -f zt-backend zt-proxy > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1

docker run -d --name zt-backend --network zt-net nginx:alpine > /dev/null
docker run -d --name zt-proxy --network zt-net \
  -v "$PWD/scripts/proxy.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:alpine > /dev/null
sleep 3

IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "zt-net").IPAddress}}' zt-proxy)
echo "proxy at $IP, sending traffic for ${DUR}s"

END=$((SECONDS + DUR))
i=0
while [ $SECONDS -lt $END ]; do
  curl -s -m 2 -o /dev/null "http://$IP/"
  i=$((i + 1))
  # every 50 requests, a health-check style exec inside the proxy
  if [ $((i % 50)) -eq 0 ]; then
    docker exec zt-proxy wget -q -T 2 -O /dev/null http://127.0.0.1/
  fi
  sleep 0.2
done

echo "sent $i requests"
docker rm -f zt-backend zt-proxy > /dev/null 2>&1
echo "containers removed"
