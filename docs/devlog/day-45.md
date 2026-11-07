# Day 45 - Latency spread
- scripts/live_repeat.sh: 8 act-mode runs with the beacon starting 31 to 45 s after container start (different phases of the 10 s window); each run unfreezes before cleanup
- Hypothesis written before testing: latency about 1 to 12 s, median about 6 to 8 s, freeze write under 2 ms
- Results (docs/results-day45.txt):
    nohup: ignoring input
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 8.04 0
    2 33 3 yes 6.24 0
    3 35 5 yes 4.12 0
    4 37 7 yes 2.18 0
    5 39 9 yes 10.28 0
    6 41 1 yes 8.28 0
    7 43 3 yes 6.22 0
- Observation: latency falls about 2 s per 2 s later in the window; offset 39 s (phase 9) gave the longest, 10.28 s, because the beacon straddled a window edge and was flagged only after the next window closed
- Caveats: 8 runs of one scripted attack, one workload and one baseline; the freeze covers the cgroup write only; latency is dominated by the 10 s window; not a detection rate
- Problems: earlier runs stalled after 4 rows because a beacon docker exec blocked on the already-frozen container; fixed with timeout 5; the first devlog was committed with only 3 rows and rebuilt afterwards
- Next: configurable window size and 5 s windows
