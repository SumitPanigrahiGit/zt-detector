# Day 40 - Learning mode
- Problem from Day 39: an image with no baseline is "unmonitored", so attacks on it go unseen
- scripts/record_py2.sh: python:alpine http.server plus client, 3 learning runs (190 s), 2 validation runs (100 s), beacon and burst attacks x3 inside the python container
- ml/evaluate_learn.py: train on the first L windows (L = 6, 12, 18; 10 s each) of a single learning run, test on separate validation runs and the attacks; 3 seeds
- Hypothesis written before testing: about 60 s of learning gives frequent false positives; 120 s or more gives near 0 and still flags burst and beacon
- Results (copied from docs/results-day40.txt):
- Caveats: one simple workload; learning runs, seeds and windows are not independent; the learning container was clean, so poisoning (an already-compromised container during learning) is untested
- Problems: none recorded
- Next: decide what to alert on during learning, and test a compromised learning period
