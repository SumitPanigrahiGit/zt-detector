// hello.bpf.c - runs every time any process calls execve()
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

// The kernel requires a license; GPL unlocks most helper functions.
char LICENSE[] SEC("license") = "GPL";

// SEC() tells the loader where to attach: the execve syscall entry.
SEC("tracepoint/syscalls/sys_enter_execve")
int hello_execve(void *ctx)
{
    bpf_printk("hello: execve called!");
    return 0;
}
