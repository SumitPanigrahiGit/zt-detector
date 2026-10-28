# Day 05 - User-space loader (libbpf skeleton)
- Wrote src/loader.c and scripts/build.sh
- bpftool gen skeleton creates ringbuf.skel.h; lifecycle is open_and_load -> attach -> poll -> destroy
- Events from the kernel ring buffer now print as PID / COMM / FILENAME
- Learned: ring_buffer__poll sleeps in epoll, so no busy-waiting
- Learned: signal handler only sets a volatile sig_atomic_t flag
- Problems: (write any error and fix, or "none")
- Next: add PPID, UID and cgroup ID to each event
