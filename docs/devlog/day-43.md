# Day 43 - Containment: freeze speed and the two-window rule
- Design decisions before testing: rule A thresholds only; first action is reversible (freeze, not kill); 24/132 jittered normal windows were flagged on Day 42, so destructive automation is not justified
- ml/freeze_bench.py: time from request until the kernel reports frozen=1 (cgroup.events), for docker CLI, Docker API over the unix socket, and a direct write to cgroup.freeze; 20 runs each
- ml/replay_2win.py: replays Day 42 data to compare acting on one flagged window against requiring two in a row
- Hypotheses written before testing: cgroup write under 1 ms, API a few ms, CLI tens of ms; the 2-window rule cuts false alarms but may miss the short beacon while burst survives
- Freeze results (docs/results-day43-freeze.txt):
    time from request until the kernel reports frozen=1 (ms, 20 runs each)
    docker CLI     median 55.45  p95 76.88  max 78.67
    docker API     median 25.70  p95 33.35  max 35.63
    cgroup.freeze  median 0.19  p95 0.33  max 0.35
    FREEZE DONE
- Replay results (docs/results-day43-replay.txt):
    learn runs [20, 20] normal sequences 4 attack recordings {'beacon': 6, 'burst': 6}
    SUMMARY (rule A thresholds, jittered learning L=12; counts over 2 learning runs x 3 seeds)
    normal windows: 132   flagged windows (act on 1): 0   alerts needing 2 in a row: 0
    beacon  recordings detected  act-on-1: 36 / 36   2-in-a-row: 36 / 36
    burst   recordings detected  act-on-1: 36 / 36   2-in-a-row: 27 / 36
    REPLAY DONE
- Caveats: WSL2 timing is noisy; freeze time covers the action only, not detection or event delivery; one simple workload; runs and seeds are not independent; no live closed-loop test yet
- Problems: replay shows 0/132 normal windows flagged but Day 42 showed 24/132 on the same fresh jitter data (unresolved, likely a difference in how learning windows were assembled); pasted replay file was partly garbled; the 2-window rule cost 9 burst detections here
- Next: live controller that listens to the loader, applies the rule and freezes, with end-to-end timing
