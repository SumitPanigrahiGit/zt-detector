# Week 1 Summary: Kernel tracing foundation

## Built
- WSL2 + Ubuntu eBPF toolchain (clang 18, libbpf, bpftool)
- Tracepoint on sys_enter_execve reading the executed filename
- Ring buffer (256 KB) streaming events to user space
- C loader using a libbpf skeleton (open, load, attach, poll, destroy)
- Event context: timestamp, PID, PPID, UID, cgroup ID, comm
- Automated smoke test

## Learned
- Verifier rules: user pointers need bpf_probe_read_user_str; stack is 512 bytes
- Ring buffer reserve/submit writes straight into shared memory
- CO-RE (BPF_CORE_READ) makes the object portable across kernels
- bpf_get_current_cgroup_id equals the inode of the cgroup v2 directory

## Problems solved
- Read-only WSL disk after interrupted apt: reinstalled on D: drive
- Truncated apt downloads: switched mirrors to HTTPS
- Garbled heredoc paste: verified files with tail and wc

## Next week
- connect, ptrace, mprotect tracepoints
- Map cgroup IDs to Docker container IDs
