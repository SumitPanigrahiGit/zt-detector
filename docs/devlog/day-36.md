# Day 36 - Real container age
- Replaced "first window of the recording = startup" with the container's real start time from container_start events (ml/graph_build.py; old behaviour kept as ZT_AGE=proxy)
- Started containers: windows anchored to the start time, window 0 is startup. Preexisting containers (preexisting:1): age unknown, no window is startup
- Sanity: ZT_AGE=proxy reproduced the Day 35 numbers exactly (docs/results-day36-proxy.txt)
- Hypothesis written before testing: on already-running containers the proxy gives false positives or hides attacks, real age does not
- scripts/record_pre.sh: 3 normal and 5 burst recordings with the loader started after the containers; ml/evaluate_pre.py compares both modes
- Results (copied from the result files):
  Existing data, real age:
    train=93 val=32 attack windows: {'beacon': 13, 'scan': 7, 'burst': 16, 'wx': 7}
    validation windows flagged: 0 / 160
    beacon  attack windows flagged: 65 / 65
    scan    attack windows flagged: 35 / 35
    burst   attack windows flagged: 75 / 80
    wx      attack windows flagged: 35 / 35
  Running containers, proxy mode:
    mode=proxy train=93 val=32 pre_norm=18 pre_burst=10
    validation windows flagged (false positives): 0 / 160
    already-running NORMAL windows flagged (false positives): 4 / 90
    already-running BURST windows flagged (detections): 35 / 50
  Running containers, real mode:
    mode=real train=93 val=32 pre_norm=18 pre_burst=10
    validation windows flagged (false positives): 0 / 160
    already-running NORMAL windows flagged (false positives): 0 / 90
    already-running BURST windows flagged (detections): 40 / 50
- Caveats: one workload and one machine; seeds are not independent samples; 8 short recordings; the real-age fix was designed from the proxy's known weakness, not tuned on these results
- Known limit: a preexisting container with unknown age cannot be told apart from a started one; a container that restarts its processes later looks like startup only if the container itself restarts
- Problems: none recorded
- Next: decide between a temporal model (TGN) and more data
