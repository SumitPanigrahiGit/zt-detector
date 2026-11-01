#!/bin/bash
# stealth.sh KIND - runs one living-off-the-land style attack inside zt-victim
# kinds: beacon  scan  burst  wx
cd "$(dirname "$0")/.."
OUT=data/stealth_$1.jsonl
docker rm -f zt-victim zt-backend > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1
sudo rm -f "$OUT"
sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
sleep 2
docker run -d --name zt-victim --network zt-net --cap-add SYS_PTRACE nginx:alpine > /dev/null
sleep 3
[ -x build/attack ] || gcc -static -O1 -o build/attack scripts/attack.c
case $1 in
  beacon) for i in 1 2 3 4 5 6; do docker exec zt-victim wget -q -T 1 -O /dev/null http://1.1.1.1:8443/; sleep 1; done ;;
  scan)   for p in 22 23 25 110 143 445 3306 5432 6379 8080; do
            docker exec zt-victim wget -q -T 1 -O /dev/null http://172.18.0.1:$p/; done ;;
  burst)  for i in $(seq 40); do docker exec zt-victim wget -q -T 1 -O /dev/null http://127.0.0.1/; done ;;
  wx)     docker cp build/attack zt-victim:/tmp/a
          docker exec zt-victim /tmp/a 1 > /dev/null ;;
esac
sleep 2
docker rm -f zt-victim > /dev/null 2>&1
sudo pkill -INT -x loader; sleep 2
sudo chmod a+r "$OUT"
wc -l "$OUT"
