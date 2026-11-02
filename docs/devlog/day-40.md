# Day 40 - Learning mode
- Problem from Day 39: an image with no baseline is "unmonitored", so attacks on it go unseen
- scripts/record_py2.sh: python:alpine http.server plus client, 3 learning runs (190 s), 2 validation runs (100 s), beacon and burst attacks x3
- ml/evaluate_learn.py: train on the first L windows (L = 6, 12, 18; 10 s each) of one learning run, test on separate validation runs and the attacks; 3 seeds
- Hypothesis written before testing: about 60 s of learning gives frequent false positives; 120 s or more gives near 0 and still flags burst and beacon
- Results (copied from docs/results-day40.txt):
    learn runs: [21, 21, 21] val windows: 22 attack windows: {'beacon': 6, 'burst': 6}
    SUMMARY (counts over learning runs x 3 seeds; L = learning windows of 10 s)
    L=6   val (false positives)  flagged: 0 / 198
    L=6   atk beacon             flagged: 0 / 54
    L=6   atk burst              flagged: 0 / 54
    L=12  val (false positives)  flagged: 0 / 198
    L=12  atk beacon             flagged: 0 / 54
    L=12  atk burst              flagged: 0 / 54
    L=18  val (false positives)  flagged: 0 / 198
    L=18  atk beacon             flagged: 0 / 54
    L=18  atk burst              flagged: 0 / 54
    EVALLEARN DONE
- Caveats: one simple workload; runs, seeds and windows are not independent; repeated recordings had identical event counts; the learning container was clean, so poisoning is untested
- Problems: devlog was first committed before the evaluation ran, so it had no results; rebuilt afterwards. evaluate_learn.py was also created late
- Next: test poisoning (attack during learning) and define alerting during learning
