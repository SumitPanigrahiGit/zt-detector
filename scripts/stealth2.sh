#!/bin/bash
# stealth2.sh KIND REP - one attack run; starts 12 s after the container so startup is its own window
cd "$(dirname "$0")/.."
OUT=data/atk_$1_$2.jsonl
docker rm -f zt-victim zt-backend zt-proxy > /dev/null 2>&1
docker network create zt-net > /dev/null 2>&1
sudo rm -f "$OUT"
sudo setsid ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 < /dev/null &
sleep 2
docker run -d --name zt-victim --network zt-net --cap-add SYS_PTRACE nginx:alpine > /dev/null
sleep 12
[ -x build/attack ] || gcc -static -O1 -o build/attack scripts/attack.c
case $1 in
  beacon) for i in 1 2 3 4 5 6; do docker exec zt-victim wget -q -T 1 -O /dev/null http://1.1.1.1:8443/ 2>/dev/null; sleep 1; done ;;
  scan)   for p in 22 23 25 110 143 445 3306 5432 6379 8080; do
            docker exec zt-victim wget -q -T 1 -O /dev/null http://172.18.0.1:$p/ 2>/dev/null; done ;;
  burst)  for i in $(seq 40); do docker exec zt-victim wget -q -T 1 -O /dev/null http://127.0.0.1/ 2>/dev/null; done ;;
  wx)     docker cp build/attack zt-victim:/tmp/a > /dev/null
          docker exec zt-victim /tmp/a 1 > /dev/null 2>&1 ;;
esac
sleep 2
docker rm -f zt-victim > /dev/null 2>&1
sudo pkill -INT -x loader; sleep 2
sudo chmod a+r "$OUT"
echo "recorded $OUT: $(wc -l < "$OUT") events"
