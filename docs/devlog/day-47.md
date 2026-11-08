# Day 47 - 5 s windows: false freezes and the learning-length fix
- Live 5 s act runs (docs/results-day47-live5.txt), per-run logs kept in /tmp/zt_ctl_run*.txt:
    nohup: ignoring input
    run offset_s phase_s frozen latency_s pclient_flagged
    1 31 1 yes 2.62 0
    2 33 3 yes 1.00 1
    3 35 5 yes 3.93 0
    4 37 7 yes 1.96 1
    5 39 9 yes 4.79 1
    6 41 1 yes 2.94 1
    REPEAT DONE
- zt-pclient was flagged in 4 of 6 runs (5 of 12 with Day 46); the same window shape (score 0.0454 vs threshold 0.0433) repeats, so it is one pattern the 12-window baseline never saw, not noise
- Offline (ml/diag_L.py, 5 s, 2 learning runs x 3 seeds): normal windows flagged of 252 = 4 at L=12, 0 at L=24, 0 at L=36
- Caveats: same baseline and seed across runs, so flags are not independent; L=24 not yet tested for attack detection or live
- Problems: none recorded
- Next: confirm attacks at L=24 offline, then rerun live 5 s with L=24
- Offline attack check at 5 s (ml/diag_L2.py): L=12 beacon 36/36, burst 33/36; L=24 beacon 36/36, burst 36/36
