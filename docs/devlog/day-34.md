# Day 34 - More data
- scripts/record_normal3.sh: 3 train runs (300 s) and 2 validation runs (150 s) of varied normal traffic, separate recordings
- scripts/stealth2.sh: each attack starts 12 s after container start; 5 repetitions per attack; the startup window is dropped from attack results
- ml/evaluate2.py: 5 seeds, threshold = 1.5 x 99th percentile of train window scores (train only)
- Results (copied from docs/results-day34.txt):
    train=93 val=32 attack windows: {'beacon': 10, 'scan': 5, 'burst': 10, 'wx': 5}
    SUMMARY (counts over 5 seeds)
    validation windows flagged: 0 / 160
    beacon  attack windows flagged: 50 / 50
    scan    attack windows flagged: 25 / 25
    burst   attack windows flagged: 20 / 50
    wx      attack windows flagged: 25 / 25
    EVAL2 DONE
- Caveats: one machine, one workload, one Docker image; counts are window-seed checks, so seeds are not independent samples
- Problems: none recorded
- Next: decide the model direction from these results
