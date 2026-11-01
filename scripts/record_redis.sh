#!/bin/bash
# record_redis.sh - 3 train runs (180 s) and 2 validation runs (120 s)
cd "$(dirname "$0")/.."
sudo -v
for spec in "r_train_1 180" "r_train_2 180" "r_train_3 180" "r_val_1 120" "r_val_2 120"; do
  set -- $spec
  sudo setsid ./build/loader -q -c -j data/$1.jsonl > /dev/null 2>&1 < /dev/null &
  sleep 2
  ./scripts/gen_redis.sh $2
  sudo pkill -INT -x loader; sleep 2
  sudo chmod a+r data/$1.jsonl
  echo "recorded $1: $(wc -l < data/$1.jsonl) events"
done
echo "REDIS DONE"
