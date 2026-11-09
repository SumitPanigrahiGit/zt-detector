# Day 49 - 2-in-a-row at 5 s (L=24)
- controller.py: --consecutive N (default 1); live_repeat.sh passes ZT_CONSEC
- Hypothesis written before testing: 0 false freezes in 6 runs; beacon latency about 5 to 8 s; misses possible
- Result (docs/results-day49-consec2.txt):
    nohup: ignoring input
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 8.19 0
    2 33 3 yes 6.50 0
    3 35 5 yes 9.50 0
    4 37 7 yes 7.51 0
    5 39 9 yes 5.48 0
    6 41 1 yes 8.48 0
    sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
    sudo: a password is required
    sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
    sudo: a password is required
- Outcome: 6/6 beacon frozen, 0/6 zt-pclient flagged, median latency 7.85 s (range 5.48 to 9.50 s); false-positive prediction held, latency slightly above the predicted range
- Comparison: 10 s L=12: 0/8 flagged, median 6.24 s; 5 s L=12: 4/6, ~2.8 s; 5 s L=24: 1/6, 2.83 s; 5 s L=24 + 2-in-a-row: 0/6, 7.85 s
- Conclusion: 2-in-a-row at 5 s is slower than plain 10 s windows with no better false-positive record in these runs
- Caveats: sudo credentials expired mid-run (sudo errors in the log), so the run is valid but suspect; 6 runs, one workload and baseline; counts, not rates
- Problems: sudo password timeout during the unattended run
- Next: choose the default (10 s windows, dry-run on) and move to verify_all checks, then the dashboard
