# Day 40 - Learning mode
- Problem from Day 39: an image with no baseline is "unmonitored", so attacks on it go unseen
- Recordings: python:alpine http.server plus client, 3 learning runs (190 s), 2 validation runs (100 s), beacon and burst attacks
- First evaluation (single threshold, docs/results-day40-single-threshold.txt): 0 flagged in every row, including beacon
- Diagnosis: startup windows (score 0.15 to 0.18) set the 99th-percentile threshold at 0.26; steady windows score 0.04 and the beacon scores 0.13 to 0.15, so every attack fell below it
- Fix: one threshold per regime (startup versus steady, from the existing startup flag), each 1.5 x max of its own training scores. Chosen after seeing attack scores, so fresh attacks (reps 4 to 6) were recorded afterwards
- Results, design set (docs/results-day40-regime.txt):
    SUMMARY (counts over learning runs x 3 seeds; L = learning windows of 10 s)
    L=6   val (false positives)  flagged: 0 / 198
    L=6   atk beacon             flagged: 54 / 54
    L=6   atk burst              flagged: 54 / 54
    L=12  val (false positives)  flagged: 0 / 198
    L=12  atk beacon             flagged: 54 / 54
    L=12  atk burst              flagged: 45 / 54
    L=18  val (false positives)  flagged: 0 / 198
    L=18  atk beacon             flagged: 54 / 54
    L=18  atk burst              flagged: 54 / 54
    EVALLEARN DONE
- Results, with fresh attacks (docs/results-day40-regime-fresh.txt):
    learn runs: [21, 21, 21] val windows: 22 attack windows: {'beacon': 12, 'burst': 12}
    SUMMARY (counts over learning runs x 3 seeds; L = learning windows of 10 s)
    L=6   val (false positives)  flagged: 0 / 198
    L=6   atk beacon             flagged: 108 / 108
    L=6   atk burst              flagged: 108 / 108
    L=12  val (false positives)  flagged: 0 / 198
    L=12  atk beacon             flagged: 108 / 108
    L=12  atk burst              flagged: 99 / 108
    L=18  val (false positives)  flagged: 0 / 198
    L=18  atk beacon             flagged: 108 / 108
    L=18  atk burst              flagged: 108 / 108
    EVALLEARN DONE
- Caveats: one simple workload; runs, seeds and windows are not independent; repeated recordings have identical event counts; poisoning untested; the regime fix has not yet been re-checked on the nginx data
- Problems: first result was an artefact of the threshold rule; evaluator and devlog were created late
- Next: re-check the nginx evaluation with regime thresholds; test poisoning
