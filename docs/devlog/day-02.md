# Day 02 - First eBPF tracepoint
- Wrote bpf/hello.bpf.c attached to sys_enter_execve
- Compiled with clang -target bpf, loaded with bpftool, saw output in trace_pipe
- Learned: the verifier checks the program before it runs in the kernel
- Learned: a tracepoint is a stable hook point built into the kernel
- Learned: bpf_printk is for debugging only; maps and ring buffers are for real data
- Problems: VS Code "another instance not responding" fixed by ending Code.exe tasks and restarting WSL
- Next: read the actual filename passed to execve
