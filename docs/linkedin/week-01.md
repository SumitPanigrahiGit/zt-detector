Week 1 update: eBPF Container Security Detector

Built the kernel tracing foundation:
- eBPF tracepoint on execve, streaming events through a ring buffer
- C loader using libbpf skeleton
- Each event carries PID, PPID, UID, cgroup ID and the executed file

Biggest bug: an interrupted apt install pushed my WSL disk into read-only mode. Fix: moved the distro to another drive.

Next week: connect, ptrace and mprotect tracing, and mapping processes to Docker containers.

GitHub: https://github.com/SumitPanigrahiGit/zt-detector

#eBPF #CloudSecurity #Linux #BuildInPublic
