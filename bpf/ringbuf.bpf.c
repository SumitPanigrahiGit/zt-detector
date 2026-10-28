// ringbuf.bpf.c - sends execve events to user space via a ring buffer
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include "common.h"

char LICENSE[] SEC("license") = "GPL";

// One ring buffer shared by all CPUs. Size must be a power of two
// and a multiple of the page size.
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);   // 256 KB
} events SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx)
{
    // Reserve space directly inside the ring buffer: no stack copy.
    struct exec_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;   // buffer full: drop the event, never block the kernel

    e->pid = bpf_get_current_pid_tgid() >> 32;   // upper 32 bits = TGID (the "PID")
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    const char *filename = (const char *)ctx->args[0];
    bpf_probe_read_user_str(&e->filename, sizeof(e->filename), filename);

    bpf_ringbuf_submit(e, 0);   // make the event visible to user space
    return 0;
}
