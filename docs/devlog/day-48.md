# Day 48 - 5 s windows with longer learning (L=24)
- baseline.py reads ZT_LEARN_L (default 12); live_repeat.sh passes it through sudo env
- Hypothesis written before testing: zt-pclient flagged in 0 of 6 runs, median latency near 3 s
- Result (docs/results-day48-L24.txt):
    nohup: ignoring input
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 2.65 0
    2 33 3 yes 1.03 0
    3 35 5 yes 4.09 0
    4 37 7 yes 1.84 1
    5 39 9 yes 5.00 0
    6 41 1 yes 3.00 0
    REPEAT DONE
- Hypothesis wrong on false positives: 1 of 6 runs flagged zt-pclient (score 0.0296 vs thr 0.0252), down from 4 of 6 at L=12; latency median 2.83 s
- Comparison: 10 s L=12: 0/8 flagged, median 6.24 s; 5 s L=12: 4/6 flagged; 5 s L=24: 1/6 flagged
- Caveats: offline replay predicted 0 flags at L=24, live fresh jitter showed one; 6 runs, one workload and baseline
- Problems: none recorded
- Next: test the 2-in-a-row rule live at 5 s, and decide the default window size
