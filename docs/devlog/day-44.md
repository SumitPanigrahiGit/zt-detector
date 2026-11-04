# Day 44 - Live controller (closed loop)
- ml/baseline.py trains the python:alpine baseline (one jittered learning run, 12 windows, seed 0) with per-regime thresholds; ml/controller.py follows the loader's JSONL, scores each closed 10 s window per container, and freezes via cgroup.freeze only with --act (dry-run default); other images are reported UNMONITORED
- Decisions before testing: dry-run default, act on one flagged window (the 2-window rule cost 9 burst detections on Day 43), reversible freeze, throwaway containers only
- Hypothesis written before testing: first beacon connect to freeze about 3 to 15 s, dominated by the 10 s window
- Dry run: 13 windows scored, 1 flagged (zt-py, score 0.1138 vs threshold 0.0251), WOULD FREEZE logged, container state frozen 0, zt-pclient never flagged
- Act run: FROZEN zt-py, write 0.746 ms, first beacon connect to frozen 4.35 s, state frozen 1; later beacon docker exec calls failed with "cannot exec in a paused container", showing the attack was interrupted
- Caveats: one run each, so 4.35 s depends on where the beacon fell in the window; the 15 ms target covers only the freeze write, not detection; one workload, image, baseline and attack; identical score in both runs shows reproducible training, not independent evidence
- Problems: none recorded
- Next: report the end-to-end time distribution over several runs, and consider shorter windows
