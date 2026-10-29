// common.h - event layout shared by kernel (eBPF) and user space
#ifndef __COMMON_H
#define __COMMON_H

#define TASK_COMM_LEN 16
#define FILENAME_LEN  128

struct exec_event {
    __u64 ts_ns;        // bpf_ktime_get_ns() at the time of the call
    __u64 cgroup_id;    // identifies the container (cgroup v2 inode number)
    __u32 pid;          // TGID, what users call "PID"
    __u32 ppid;         // parent's TGID
    __u32 uid;
    __u32 _pad;         // explicit padding keeps layout identical on both sides
    char  comm[TASK_COMM_LEN];
    char  filename[FILENAME_LEN];
};

#endif
