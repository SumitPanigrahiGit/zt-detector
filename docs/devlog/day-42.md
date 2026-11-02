# Day 42 - Variation-aware threshold and learning report
- Recorded fresh jittered learning runs (pyjl_1, pyjl_2) and fresh jittered validation (pyj_3, pyj_4); the rule was validated on data not used to find the problem
- ml/evaluate_thr.py: rule A = 1.5 x max steady training score; rule B = mean + 3 sd of scores on held-out steady learning windows
- ml/learning_report.py: lists programs and destinations first seen during learning, so a poisoned baseline can be reviewed
- Hypotheses written before testing: rule B cuts jitter false positives without losing the beacon; no threshold rule fixes poisoning
- Results (copied from docs/results-day42.txt):
    jitter learn runs [20, 20] fresh jitter windows 22 beacon windows 12
    SUMMARY (L=12, jittered learning, counts over runs x 3 seeds)
    fresh jitter val  rule A (1.5 x max): flagged 24 / 132   rule B (held-out mean+3sd): flagged 24 / 132
    beacon            rule A (1.5 x max): flagged 72 / 72   rule B (held-out mean+3sd): flagged 72 / 72
    EVALTHR DONE
- Caveats: one simple workload; 2 learning runs and 3 seeds are not independent; rule B uses few held-out windows, so it is noisy; k=3 was fixed before testing, not tuned
- Problems: hypothesis 1 not supported (rule A and B gave identical counts, possibly because rule B fell back to rule A with few held-out windows); jitter false positives fell mainly because the learning data was jittered; a garbled paste damaged evaluate_thr.py during creation
- Next: fold the threshold rule and learning report into the loader/controller design
