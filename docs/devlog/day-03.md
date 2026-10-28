# Day 03 - Reading execve filename
- Inspected tracepoint format under /sys/kernel/debug/tracing/events (filename at offset 16)
- Read args[0] (filename) with bpf_probe_read_user_str
- Learned: user pointers must be copied with bpf_probe_read_user*, never dereferenced
- Learned: eBPF stack is limited to 512 bytes
- Problems: compile failed because the source file was not created yet; created it and recompiled
- Next: send events to user space with a ring buffer
