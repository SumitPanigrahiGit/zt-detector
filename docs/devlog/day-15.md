# Day 15 - Per-container event counters
- Added a stats table (256 entries) keyed by cgroup ID with counts per event type
- Added -q flag (quiet: only the summary); summary table printed on Ctrl+C
- Counts are recorded after the -c filter, so -c -q gives a container-only summary
- Learned: per-container counts are the first behavioural feature for the ML phase
- Learned: counts need a time window (rates per interval) to be useful for anomaly detection
- Problems: long pastes got garbled, so the patch moved into a file; ran docker commands in Windows cmd by mistake (wrong daemon)
- Next: IPv6 connect
