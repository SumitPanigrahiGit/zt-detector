# Day 17 - Overhead measurement
- Added scripts/bench.sh: baseline vs traced workload, loader CPU from /proc/<pid>/stat, per-event cost from bpf_stats
- Results, 3 runs, WSL2, 3000 execs of /bin/true:
  - Loader CPU idle: 0.000%, 0.100%, 0.000% of one core
  - Loader CPU under the exec storm: 1.606%, 1.213%, 1.449% of one core
  - Kernel cost: about 3.3 to 6.4 microseconds per event (counters accumulate across runs, bpf_stats adds its own cost)
  - Workload slowdown: not measurable; negative values are noise
- Note: this script was first run later, during the Day 20 consolidation, not on Day 17 itself
- Learned: exec-storm is a worst case; report overhead together with the event rate
