#!/bin/bash
# record_normal3.sh - 3 train runs and 2 validation runs of varied normal traffic
cd "$(dirname "$0")/.."
sudo -v
for spec in "n3_train_1 300" "n3_train_2 300" "n3_train_3 300" "n3_val_1 150" "n3_val_2 150"; do
  set -- $spec
  sudo setsid ./build/loader -q -c -j data/$1.jsonl > /dev/null 2>&1 < /dev/null &
  sleep 2
  ./scripts/gen_normal2.sh $2
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r data/$1.jsonl
  echo "recorded $1: $(wc -l < data/$1.jsonl) events"
done
echo "NORMAL DONE"
