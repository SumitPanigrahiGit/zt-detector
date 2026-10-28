// execve.bpf.c - prints the filename of every execve() call
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

char LICENSE[] SEC("license") = "GPL";

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx)
{
    // args[0] is the first syscall argument: const char *filename
    const char *filename = (const char *)ctx->args[0];

    // Stack buffer (eBPF stack limit is 512 bytes, so keep it small)
    char buf[128];

    // Safely copy the string from user memory. A direct dereference
    // would be rejected by the verifier.
    long len = bpf_probe_read_user_str(buf, sizeof(buf), filename);
    if (len < 0)
        return 0;

    bpf_printk("execve: %s", buf);
    return 0;
}
