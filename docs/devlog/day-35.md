# Day 35 - Container-age feature
- Diagnosis: steady-state windows have at most 3 spawn edges; startup windows reach 22 (nginx entrypoint scripts). The baseline therefore treated up to 22 spawns as normal, hiding the burst attack (12 to 28 spawns per window)
- Fix: is_startup feature (first window of a container's recording) on every node. Startup windows stay in training, so container launches do not raise false alarms
- Results: burst 20/50 -> 47/50 window-seed checks; validation 0/160 before and after; beacon, scan, wx all flagged
- Fresh attack runs (burst 6 to 8, others 6 to 7) were recorded after the fix was chosen: burst 29/30 of the new checks, overall burst 76/80; validation still 0/160
- Caveats: seed 2 is the weakest (7/10 and 12/16); seeds are not independent samples; 16 burst windows come from 8 recordings; one workload, one machine
- Known limit: startup is inferred from position in the recording, not from the real container start time
- Problems: none recorded
- Next: derive container age from container_start events
