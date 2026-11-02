# Day 38 - Per-service baselines
- Finding from Day 37: the combined nginx+redis model dropped burst detection from 75/80 to 59/80 (redis windows contain more spawns, widening normal)
- ml/evaluate_ps.py: one model and threshold per service; services mapped from container names (stand-in for the image name, to be read by the loader on Day 39)
- Hypothesis written before testing: per-service models restore burst detection and keep redis false positives near 0; a model on the wrong service flags nearly everything
- Results (copied from docs/results-day38.txt):
    SUMMARY (counts over 5 seeds)
    nginx model: nginx val                     flagged: 0 / 160
    nginx model: atk beacon                    flagged: 65 / 65
    nginx model: atk scan                      flagged: 35 / 35
    nginx model: atk burst                     flagged: 75 / 80
    nginx model: atk wx                        flagged: 35 / 35
    nginx model: redis val (wrong service)     flagged: 140 / 140
    redis model: redis val                     flagged: 0 / 140
    redis model: nginx val (wrong service)     flagged: 158 / 160
    EVALPS DONE
- Caveats: two workloads, one machine, non-independent seeds; attack recordings come from the nginx image only; redis baseline is small
- Problems: none recorded
- Next: loader reads the image name; define behaviour for images with no baseline
