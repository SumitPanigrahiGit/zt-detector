#!/bin/bash
# demo_attack.sh [OUT.jsonl] - stages a hijack of an nginx container and runs the rules on it
cd "$(dirname "$0")/.."
OUT=${1:-data/attack_demo.jsonl}
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
sudo mount -t bpf bpf /sys/fs/bpf 2>/dev/null
[ -x build/attack ] || gcc -static -O1 -o build/attack scripts/attack.c

docker rm -f zt-victim > /dev/null 2>&1
sudo rm -f "$OUT"
sudo setsid ./build/loader -q -c -j "$OUT" > /tmp/zt_demo_out.txt 2>&1 < /dev/null &
sleep 2

docker run -d --name zt-victim --cap-add SYS_PTRACE nginx:alpine > /dev/null
sleep 3
echo "-- attacker actions inside zt-victim --"
docker cp build/attack zt-victim:/tmp/attack
docker exec zt-victim /tmp/attack 1
sleep 1
docker rm -f zt-victim > /dev/null
sleep 1

sudo pkill -INT -x loader
sleep 1.5
sudo chmod a+r "$OUT"
echo "-- detections --"
python3 scripts/detect_rules.py data/normal_train.jsonl "$OUT" zt-victim
