# Day 46 - 5 s windows (offline part)
- WINDOW_NS now comes from ZT_WINDOW_S (default 10); the 10 s replay reproduced Day 43 exactly
- Hypothesis written before testing: median latency about halves; false positives rise above 0
- Offline results (docs/results-day46-fp.txt):
    SUMMARY (rule A thresholds, jittered learning L=12; counts over 2 learning runs x 3 seeds)
    normal windows: 252   flagged windows (act on 1): 4   alerts needing 2 in a row: 0
    beacon  recordings detected  act-on-1: 36 / 36   2-in-a-row: 36 / 36
    burst   recordings detected  act-on-1: 33 / 36   2-in-a-row: 30 / 36
    REPLAY DONE
- Observation: at 5 s, 4 of 252 normal windows were flagged (0 of 132 at 10 s); burst fell to 33/36; requiring 2 in a row removed all 4 false positives at a cost of 3 burst detections
- Caveats: window-seed counts are not independent; live latency at 5 s not yet measured
- Problems: none recorded
- Next: identify the 4 flagged windows, then measure live latency at 5 s (sudo env ZT_WINDOW_S=5)
