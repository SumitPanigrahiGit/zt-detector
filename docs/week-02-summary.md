# Week 2 Summary: Multi-syscall tracing and container attribution

## Built
- One tagged-union event struct shared by kernel and user space
- Tracepoints: execve, connect (IPv4), ptrace, mprotect (PROT_EXEC only)
- Docker installed in WSL2 (systemd enabled)
- cgroup ID to container ID and name resolution, with cache, rescan rate limit and stale-entry pruning
- -c flag for container-only events
- Smoke test covering host and container events

## Learned
- The kernel knows cgroup IDs; names are resolved in user space
- Filtering in the kernel (mprotect) reduces ring buffer load
- ptrace attach plus memory writes and W+X mprotect are classic injection signals
- A container is a normal process tree on the host

## Problems solved
- systemd missing in WSL, so docker service failed: enabled it in /etc/wsl.conf and restarted from Windows cmd
- Stale cache after container deletion: prune on rescan

## Next week (Week 3)
- IPv6 connect, more syscalls where useful
- Per-container event statistics
- Overhead measurement
