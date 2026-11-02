# Day 41 - Jitter and poisoning
- scripts/record_py4.sh: 2 jittered validation runs (random paths, 1 to 3 s random sleeps, occasional extra request) and 2 poisoned learning runs (beacon to 1.1.1.1:8443 every 5 s during learning)
- ml/evaluate_poison.py: L=12 learning windows, per-regime thresholds as on Day 40, 3 seeds
- Hypotheses written before testing: jitter gives false positives on a perfectly regular baseline; a beacon present during learning is absorbed and a later beacon is missed
- Results (copied from docs/results-day41.txt):
- Caveats: one simple workload; runs, seeds and windows are not independent; one poisoning pattern (periodic beacon); no repeated poisoned recordings beyond two
- Problems: none recorded
- Next: decide mitigations for poisoning and a less brittle threshold, validated on fresh data
