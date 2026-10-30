# Day 06 - Process context (PPID, UID, cgroup ID)
- Extended the event struct with ts_ns, cgroup_id, ppid, uid
- PPID read with BPF_CORE_READ(task, real_parent, tgid)
- bpf_get_current_cgroup_id() matches the inode of the cgroup v2 directory
- Learned: CO-RE lets one compiled eBPF object adapt to different kernel layouts
- Learned: pid_tgid upper 32 bits = TGID, uid_gid lower 32 bits = UID
- Problems: a pasted heredoc got garbled and truncated the .c file; recreated it and checked it with tail and wc
- Next: cleanup, smoke test, tag v0.1
