# Day 25 - Kernel-to-user-space latency
- record_latency() subtracts the kernel event timestamp (bpf_ktime_get_ns) from CLOCK_MONOTONIC at the start of the event callback
- Samples are stored (up to 200000), sorted at exit, and printed as n, p50, p99, max in microseconds
- Added check 9 to verify_all.sh: more than 100 samples and p99 under 100 ms
- Results: (fill in) idle-ish check 9 p50/p99, and the nginx load run p50/p99
- Learned: report percentiles, not averages; the kernel timestamp is taken at event creation, so this is a lower bound on end-to-end latency
- Known limits: does not include model inference or containment time; WSL2 timing is noisy
- Problems: none recorded
- Next: Phase 1 attack-simulation demo
