# Day 46 - 5 s windows
- WINDOW_NS comes from ZT_WINDOW_S (default 10); the 10 s replay reproduced Day 43 exactly; live scripts pass it with sudo env
- Hypothesis written before testing: median latency about halves (about 3 s); false positives rise above 0
- Offline results (docs/results-day46-fp.txt):
    SUMMARY (rule A thresholds, jittered learning L=12; counts over 2 learning runs x 3 seeds)
    normal windows: 252   flagged windows (act on 1): 4   alerts needing 2 in a row: 0
    beacon  recordings detected  act-on-1: 36 / 36   2-in-a-row: 36 / 36
    burst   recordings detected  act-on-1: 33 / 36   2-in-a-row: 30 / 36
    REPLAY DONE
- Offline observation: 4 window-seed flags of 252 checks, which are only 2 distinct windows (all steady, all from learning run 1); burst fell to 33/36; requiring 2 in a row removed all flags at a cost of 3 burst detections
- Live results at 5 s (docs/results-day46-live.txt):
    nohup: ignoring input
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 2.98 0
    2 33 3 yes 1.28 0
    3 35 5 yes 3.16 1
    4 37 7 yes 1.89 0
    5 39 9 yes 5.21 0
    6 41 1 yes 3.63 0
    REPEAT DONE
- Caveats: 6 runs of one scripted attack, one workload and baseline; flagged-window counts are not independent; the freeze covers the cgroup write only
- Problems: run 3 of the live 5 s test flagged zt-pclient (a normal container), which act mode would have frozen; offsets and window count are small, so this shows a cost, not a rate
- Next: choose the window size from the measured trade-off
