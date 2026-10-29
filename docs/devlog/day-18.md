# Day 18 - Dropped event counter
- Added a BPF_MAP_TYPE_PERCPU_ARRAY "drops" incremented whenever bpf_ringbuf_reserve fails
- Loader sums the per-CPU slots on exit and prints the total
- Test A: 200 execs, drops = 0. Test B: loader frozen with SIGSTOP, 3000 execs, drops = X (replace X)
- Learned: per-CPU maps avoid races without atomics; user space reads one value per possible CPU
- Learned: a security tool must report its own blind spots, not hide them
- Problems: (write any error and fix, or "none")
- Next: write events as JSON lines for the ML phase
