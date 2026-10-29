// ringbuf.bpf.c - execve and connect events with process context
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include "common.h"

#define AF_INET 2   // not provided by vmlinux.h (it is a macro)

char LICENSE[] SEC("license") = "GPL";

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Reserve an event and fill the fields common to every syscall.
static __always_inline struct event *new_event(__u32 type)
{
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return NULL;   // buffer full: drop, never block the kernel

    struct task_struct *task = (struct task_struct *)bpf_get_current_task();

    e->ts_ns     = bpf_ktime_get_ns();
    e->cgroup_id = bpf_get_current_cgroup_id();
    e->type      = type;
    e->pid       = bpf_get_current_pid_tgid() >> 32;
    e->ppid      = BPF_CORE_READ(task, real_parent, tgid);
    e->uid       = (__u32)bpf_get_current_uid_gid();
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    return e;
}

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx)
{
    struct event *e = new_event(EVT_EXEC);
    if (!e)
        return 0;

    const char *filename = (const char *)ctx->args[0];
    bpf_probe_read_user_str(&e->exec.filename, sizeof(e->exec.filename), filename);

    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_connect")
int trace_connect(struct trace_event_raw_sys_enter *ctx)
{
    // connect(int fd, const struct sockaddr *uservaddr, int addrlen)
    const void *uaddr = (const void *)ctx->args[1];

    // Step 1: read only the address family (first 2 bytes)
    __u16 family = 0;
    if (bpf_probe_read_user(&family, sizeof(family), uaddr) < 0)
        return 0;
    if (family != AF_INET)      // IPv4 only for now; IPv6 comes later
        return 0;

    // Step 2: now we know the layout, read the full sockaddr_in
    struct sockaddr_in sin = {};
    if (bpf_probe_read_user(&sin, sizeof(sin), uaddr) < 0)
        return 0;

    struct event *e = new_event(EVT_CONNECT);
    if (!e)
        return 0;

    e->connect.family = family;
    e->connect.daddr  = sin.sin_addr.s_addr;
    e->connect.dport  = sin.sin_port;

    bpf_ringbuf_submit(e, 0);
    return 0;
}

SEC("tracepoint/syscalls/sys_enter_ptrace")
int trace_ptrace(struct trace_event_raw_sys_enter *ctx)
{
    // ptrace(long request, long pid, unsigned long addr, unsigned long data)
    struct event *e = new_event(EVT_PTRACE);
    if (!e)
        return 0;

    e->ptrace.request    = (__u32)ctx->args[0];
    e->ptrace.target_pid = (__u32)ctx->args[1];

    bpf_ringbuf_submit(e, 0);
    return 0;
}
