# Day 45 - Latency spread
- scripts/live_repeat.sh: 8 act-mode runs with the beacon starting 31 to 45 s after container start (different phases of the 10 s window); each run unfreezes before cleanup
- Hypothesis written before testing: latency about 1 to 12 s, median about 6 to 8 s, freeze write under 2 ms
- Results (docs/results-day45.txt):
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 8.25 0
    2 33 3 yes 6.39 0
    3 35 5 yes 4.58 0
    4 37 7 yes 2.23 0
- Caveats: 8 runs of one scripted attack, one workload and one baseline; the freeze covers the cgroup write only and the latency is dominated by the window; not a detection rate
- Problems: none recorded
- Next: 5 s windows (needs a retrained baseline) and their false-positive cost
