# Day 08 - Unified event struct + connect tracing
- Replaced exec_event with a tagged union: struct event { type, common fields, union payload }
- Added tracepoint sys_enter_connect (IPv4 only for now)
- Read sockaddr in two steps: family first, then the full sockaddr_in
- Loader prints TYPE / PID / PPID / UID / CGROUP_ID / COMM / DETAIL
- Learned: network port and address are in network byte order, so user space uses ntohs/inet_ntop
- Learned: one ring buffer with a type field keeps event order across syscalls
- Problems: (write any error and fix, or "none")
- Next: ptrace tracing
