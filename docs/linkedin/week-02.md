Week 2 update: eBPF Container Security Detector

This week the tracer learned to see containers:
- Four syscalls traced: execve, connect, ptrace, mprotect (executable memory)
- One ring buffer, one event format for all of them
- Events are attributed to the Docker container (ID and name) via the cgroup ID
- Tested by simulating the injection pattern: RW memory made RWX flags W+X

Biggest lesson: a container is just a normal process tree. The cgroup ID is what identifies it.

Next: overhead measurement and per-container statistics.

GitHub: https://github.com/SumitPanigrahiGit/zt-detector

#eBPF #CloudSecurity #Docker #Linux #BuildInPublic
