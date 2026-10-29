# Day 10 - mprotect tracing
- Added tracepoint sys_enter_mprotect, filtered to calls with PROT_EXEC
- Loader prints addr, len and R/W/X flags, and highlights W+X
- Tested by mmap(RW) then mprotect(RWX) from python3 ctypes
- Learned: shellcode injection needs memory that is written and then executed
- Learned: filtering in the kernel reduces ring buffer load and user-space work
- Problems: (write any error and fix, or "none")
- Next: install Docker and see a container's cgroup ID
