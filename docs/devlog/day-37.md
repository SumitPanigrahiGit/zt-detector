# Day 37 - Second workload (Redis)
- scripts/gen_redis.sh, scripts/record_redis.sh: redis server plus a client running one redis-benchmark every 2 s; 3 train runs (180 s) and 2 validation runs (120 s)
- ml/evaluate_ws.py: model trained on nginx only versus nginx plus redis; threshold from train only; 5 seeds
- Hypothesis written before testing: nginx-only flags most redis windows; the combined model flags few and still detects attacks
- Results (copied from docs/results-day37.txt):
    nginx train=93 val=32 | redis train=57 val=28
    SUMMARY (counts over 5 seeds)
    nginx-only nginx val    flagged: 0 / 160
    nginx-only redis val    flagged: 140 / 140
    nginx-only atk beacon   flagged: 65 / 65
    nginx-only atk scan     flagged: 35 / 35
    nginx-only atk burst    flagged: 75 / 80
    nginx-only atk wx       flagged: 35 / 35
    both       nginx val    flagged: 0 / 160
    both       redis val    flagged: 1 / 140
    both       atk beacon   flagged: 65 / 65
    both       atk scan     flagged: 35 / 35
    both       atk burst    flagged: 59 / 80
    both       atk wx       flagged: 35 / 35
    EVALWS DONE
- Caveats: two workloads only, both on one machine; seeds are not independent samples; the attack recordings come from the nginx image, so attacks on redis are untested
- Problems: none recorded
- Next: decide per-service baselines versus one shared model
