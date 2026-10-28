# Day 04 - Kernel-side ring buffer
- Created bpf/common.h (shared exec_event struct) and bpf/ringbuf.bpf.c
- BPF_MAP_TYPE_RINGBUF (256 KB) filled with pid, comm, filename per execve
- Verified with bpftool map show and prog run_cnt (bpf_stats_enabled)
- Learned: bpf_ringbuf_reserve writes straight into shared memory, avoiding the 512-byte stack
- Learned: if the buffer is full, reserve returns NULL and we drop the event
- Problems: (write any error and fix, or "none")
- Next: user-space loader in C using libbpf skeleton to read the ring buffer
