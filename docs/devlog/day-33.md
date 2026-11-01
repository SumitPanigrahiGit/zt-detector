# Day 33 - Window-level rate features
- Added three features to every node in ml/encode.py: log1p of exec (spawned) edges, process nodes and connect edges in the window
- Same data, seeds, model and threshold rule as Day 32; results in docs/results-day33.txt, previous in docs/results-day32-before-rate.txt
- Result: burst flagged 2/2, 1/2, 1/2 windows across seeds 0,1,2 (before: 0/2 on every seed); validation false positives 0/26 on every seed; beacon, scan and wx still flagged
- Caveats: only 2 burst windows and one workload, results differ between seeds, so this is anecdotal; the threshold was not tuned on attacks
- Problems: none recorded
- Next: more varied data so conclusions do not rest on 1 or 2 windows
