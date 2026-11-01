# Day 35 - Container-age feature
- Diagnosis: steady-state windows have at most 3 spawn edges; startup windows reach 22 (nginx entrypoint scripts). The baseline therefore treated up to 22 spawns as normal, which hid the burst attack (12 to 28 spawns per window)
- Fix: is_startup feature (first window of a container's recording) on every node; startup and steady state are modelled as separate normals. Startup windows are not removed from training, so container launches do not raise false alarms
- Honesty: the fix was chosen after seeing burst results, so fresh attack runs 6 to 8 were recorded afterwards
- Results before (docs/results-day34-before-age.txt) and after (docs/results-day35.txt, docs/results-day35-fresh.txt)
- Caveats: one workload, one machine; startup is detected only by position in the recording
- Problems: none recorded
- Next: derive container age from container_start events instead of recording position
