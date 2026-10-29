// common.h - event layout shared by kernel (eBPF) and user space
#ifndef __COMMON_H
#define __COMMON_H

#define TASK_COMM_LEN 16
#define FILENAME_LEN  128

enum event_type {
    EVT_EXEC     = 1,
    EVT_CONNECT  = 2,
    EVT_PTRACE   = 3,   // Day 9
    EVT_MPROTECT = 4,   // Day 10
};

struct event {
    __u64 ts_ns;
    __u64 cgroup_id;
    __u32 type;         // enum event_type
    __u32 pid;          // TGID
    __u32 ppid;
    __u32 uid;
    char  comm[TASK_COMM_LEN];

    // Payload depends on "type"
    union {
        struct { char filename[FILENAME_LEN]; } exec;
        struct { __u32 daddr; __u16 dport; __u16 family; } connect;   // network byte order
        struct { __u32 request; __u32 target_pid; } ptrace;
        struct { __u64 addr; __u64 len; __u32 prot; __u32 _pad; } mprotect;
    };
};

#endif
