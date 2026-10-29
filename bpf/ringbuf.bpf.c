// ringbuf.bpf.c - execve and connect events with process context
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include "common.h"

#define AF_INET6 10
#define AF_INET 2   // not provided by vmlinux.h (it is a macro)

char LICENSE[] SEC("license") = "GPL";

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

// Counts events lost because the ring buffer was full.
// Per-CPU: each CPU increments its own slot, so no locking is needed.
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} drops SEC(".maps");

// Reserve an event and fill the fields common to every syscall.
static __always_inline struct event *new_event(__u32 type)
{
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) {
        // Buffer full: count the loss, never block the kernel.
        __u32 k = 0;
        __u64 *cnt = bpf_map_lookup_elem(&drops, &k);
        if (cnt)
            (*cnt)++;
        return NULL;
    }

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
    const char *uaddr = (const char *)ctx->args[1];

    __u16 family = 0;
    if (bpf_probe_read_user(&family, sizeof(family), uaddr) < 0)
        return 0;

    if (family == AF_INET) {
        struct sockaddr_in sin = {};
        if (bpf_probe_read_user(&sin, sizeof(sin), uaddr) < 0)
            return 0;

        struct event *e = new_event(EVT_CONNECT);
        if (!e)
            return 0;
        __builtin_memset(e->connect.daddr6, 0, sizeof(e->connect.daddr6));
        e->connect.family = family;
        e->connect.daddr  = sin.sin_addr.s_addr;
        e->connect.dport  = sin.sin_port;
        bpf_ringbuf_submit(e, 0);
        return 0;
    }

    if (family == AF_INET6) {
        // sockaddr_in6: family(2) port(2) flowinfo(4) addr(16) scope_id(4)
        __u16 port = 0;
        __u8 addr6[16] = {};
        if (bpf_probe_read_user(&port, sizeof(port), uaddr + 2) < 0)
            return 0;
        if (bpf_probe_read_user(addr6, sizeof(addr6), uaddr + 8) < 0)
            return 0;

        struct event *e = new_event(EVT_CONNECT);
        if (!e)
            return 0;
        __builtin_memcpy(e->connect.daddr6, addr6, sizeof(addr6));
        e->connect.family = family;
        e->connect.daddr  = 0;
        e->connect.dport  = port;
        bpf_ringbuf_submit(e, 0);
        return 0;
    }

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

#define PROT_EXEC 0x4

SEC("tracepoint/syscalls/sys_enter_mprotect")
int trace_mprotect(struct trace_event_raw_sys_enter *ctx)
{
    // mprotect(void *addr, size_t len, int prot)
    __u32 prot = (__u32)ctx->args[2];

    // Only report calls that make memory executable (cuts noise a lot)
    if (!(prot & PROT_EXEC))
        return 0;

    struct event *e = new_event(EVT_MPROTECT);
    if (!e)
        return 0;

    e->mprotect.addr = ctx->args[0];
    e->mprotect.len  = ctx->args[1];
    e->mprotect.prot = prot;
    e->mprotect._pad = 0;

    bpf_ringbuf_submit(e, 0);
    return 0;
}
