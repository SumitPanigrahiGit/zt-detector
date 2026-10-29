# 1) common.h
s = open("bpf/common.h").read()
if "daddr6" not in s:
    old = "struct { __u32 daddr; __u16 dport; __u16 family; } connect;"
    assert s.count(old) == 1, "common.h anchor not found"
    s = s.replace(old, "struct { __u8 daddr6[16]; __u32 daddr; __u16 dport; __u16 family; } connect;")
    open("bpf/common.h", "w").write(s)
    print("common.h patched")

# 2) eBPF program
s = open("bpf/ringbuf.bpf.c").read()
if "AF_INET6" not in s:
    assert s.count("#define AF_INET 2") == 1, "bpf anchor not found"
    s = s.replace("#define AF_INET 2", "#define AF_INET6 10\n#define AF_INET 2")
    start = s.index('SEC("tracepoint/syscalls/sys_enter_connect")')
    end = s.index('SEC("tracepoint/syscalls/sys_enter_ptrace")')
    new_connect = r'''SEC("tracepoint/syscalls/sys_enter_connect")
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

'''
    s = s[:start] + new_connect + s[end:]
    open("bpf/ringbuf.bpf.c", "w").write(s)
    print("ringbuf.bpf.c patched")

# 3) loader: patch only the LAST "case EVT_CONNECT" (the one in handle_event)
s = open("src/loader.c").read()
if "[%s]:%u" not in s:
    start = s.rindex("    case EVT_CONNECT: {")
    end = s.index("    case EVT_PTRACE:", start)
    new_case = r'''    case EVT_CONNECT: {
        char ip[INET6_ADDRSTRLEN];
        kind = "CONNECT";
        if (e->connect.family == 10) {
            inet_ntop(AF_INET6, e->connect.daddr6, ip, sizeof(ip));
            snprintf(detail, sizeof(detail), "[%s]:%u", ip, ntohs(e->connect.dport));
        } else {
            struct in_addr a = { .s_addr = e->connect.daddr };
            inet_ntop(AF_INET, &a, ip, sizeof(ip));
            snprintf(detail, sizeof(detail), "%s:%u", ip, ntohs(e->connect.dport));
        }
        break;
    }
'''
    s = s[:start] + new_case + s[end:]
    open("src/loader.c", "w").write(s)
    print("loader.c patched")

print("done")
