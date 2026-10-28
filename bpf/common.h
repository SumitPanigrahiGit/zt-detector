// common.h - event layout shared by kernel (eBPF) and user space
#ifndef __COMMON_H
#define __COMMON_H

#define TASK_COMM_LEN 16
#define FILENAME_LEN  128

struct exec_event {
    __u32 pid;
    char  comm[TASK_COMM_LEN];
    char  filename[FILENAME_LEN];
};

#endif
