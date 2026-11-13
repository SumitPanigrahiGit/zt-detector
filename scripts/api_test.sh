#!/bin/bash
# api_test.sh - starts the API, checks each endpoint, freezes a throwaway container and unfreezes it via the API
cd "$(dirname "$0")/.."
sudo -v
docker rm -f zt-api-t > /dev/null 2>&1
sudo pkill -f "uvicorn api.app" 2> /dev/null
docker run -d --name zt-api-t alpine sleep 300 > /dev/null
sudo setsid ./build/loader -q -c -j /tmp/zt_live.jsonl > /dev/null 2>&1 < /dev/null &
sleep 3
sudo chmod a+r /tmp/zt_live.jsonl
docker run -d --name zt-api-t2 alpine sleep 5 > /dev/null
sleep 2
sudo setsid .venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000 > /tmp/zt_api.txt 2>&1 < /dev/null &
sleep 4
FAIL=0
for p in health events containers alerts; do
  T=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" http://127.0.0.1:8000/$p)
  echo "GET /$p -> $T"
  case "$T" in 200*) ;; *) FAIL=1 ;; esac
done
CID=$(docker inspect -f '{{.Id}}' zt-api-t)
sudo sh -c "echo 1 > /sys/fs/cgroup/system.slice/docker-$CID.scope/cgroup.freeze"
echo "before: $(grep frozen /sys/fs/cgroup/system.slice/docker-$CID.scope/cgroup.events)"
echo "POST unfreeze -> $(curl -s -X POST http://127.0.0.1:8000/unfreeze/zt-api-t)"
echo "after:  $(grep frozen /sys/fs/cgroup/system.slice/docker-$CID.scope/cgroup.events)"
echo "bad name -> $(curl -s -o /dev/null -w '%{http_code}' -X POST 'http://127.0.0.1:8000/unfreeze/..%2Fetc')"
echo "unknown -> $(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/unfreeze/no-such-ct)"
sudo pkill -f "uvicorn api.app"
sudo pkill -INT -x loader
docker rm -f zt-api-t zt-api-t2 > /dev/null 2>&1
[ "$FAIL" = 0 ] && echo "API TEST DONE" || echo "API TEST: an endpoint failed"
