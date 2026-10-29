#!/bin/bash
# record.sh NAME SECONDS - records container events while generating normal traffic
cd "$(dirname "$0")/.."
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
sudo mount -t bpf bpf /sys/fs/bpf 2>/dev/null
OUT=data/$1.jsonl
DUR=${2:-120}
sudo ./build/loader -q -c -j "$OUT" > /dev/null 2>&1 &
sleep 2
./scripts/gen_normal.sh "$DUR"
sudo pkill -INT -x loader
sleep 1.5
python3 scripts/summarize.py "$OUT"
