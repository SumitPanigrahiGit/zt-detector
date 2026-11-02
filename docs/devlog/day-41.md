# Day 41 - Jitter and poisoning
- scripts/record_py4.sh: 2 jittered validation runs and 2 poisoned learning runs (beacon to 1.1.1.1:8443 every 5 s during learning)
- ml/evaluate_poison.py: L=12 learning windows, per-regime thresholds as on Day 40, 3 seeds
- Hypotheses written before testing: jitter gives false positives on a perfectly regular baseline; a beacon present during learning is absorbed and a later beacon is missed
- Results (copied from docs/results-day41.txt):
- Caveats: one simple workload; runs, seeds and windows are not independent; one poisoning pattern; two poisoned recordings
- Problems: pasted scripts were garbled, so the evaluator was recreated in parts; the first devlog was committed before any results existed
- Next: decide mitigations from these results
