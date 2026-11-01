#!/bin/bash
# gen_redis.sh SECONDS - redis server plus a client that benchmarks it every 2 s
cd "$(dirname "$0")/.."
DUR=${1:-180}
docker rm -f zt-redis zt-rclient > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1
docker run -d --name zt-redis --network zt-net redis:alpine > /dev/null
sleep 3
docker run -d --name zt-rclient --network zt-net redis:alpine sh -c 'while true; do redis-benchmark -h zt-redis -c 3 -n 300 -q -t set,get > /dev/null 2>&1; sleep 2; done' > /dev/null
sleep "$DUR"
docker rm -f zt-redis zt-rclient > /dev/null 2>&1
