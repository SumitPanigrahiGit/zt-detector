// loader.c - loads ringbuf.bpf.o and prints execve/connect events
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <linux/types.h>
#include <bpf/libbpf.h>
#include "common.h"
#include "ringbuf.skel.h"

static volatile sig_atomic_t stop = 0;
static void on_signal(int sig) { (void)sig; stop = 1; }

static const char *ptrace_name(unsigned int r)
{
    switch (r) {
    case 0:      return "TRACEME";
    case 1:      return "PEEKTEXT";
    case 2:      return "PEEKDATA";
    case 4:      return "POKETEXT";
    case 5:      return "POKEDATA";
    case 7:      return "CONT";
    case 8:      return "KILL";
    case 9:      return "SINGLESTEP";
    case 12:     return "GETREGS";
    case 13:     return "SETREGS";
    case 16:     return "ATTACH";
    case 17:     return "DETACH";
    case 0x4206: return "SEIZE";
    default:     return "OTHER";
    }
}

static void prot_str(unsigned int p, char *out)
{
    out[0] = (p & 1) ? 'R' : '-';
    out[1] = (p & 2) ? 'W' : '-';
    out[2] = (p & 4) ? 'X' : '-';
    out[3] = '\0';
}

static int handle_event(void *ctx, void *data, size_t size)
{
    const struct event *e = data;
    const char *kind;
    char detail[160];

    if (size < sizeof(*e))
        return 0;

    switch (e->type) {
    case EVT_EXEC:
        kind = "EXEC";
        snprintf(detail, sizeof(detail), "%s", e->exec.filename);
        break;
    case EVT_CONNECT: {
        char ip[INET_ADDRSTRLEN];
        struct in_addr a = { .s_addr = e->connect.daddr };
        inet_ntop(AF_INET, &a, ip, sizeof(ip));
        kind = "CONNECT";
        snprintf(detail, sizeof(detail), "%s:%u", ip, ntohs(e->connect.dport));
        break;
    }
    case EVT_PTRACE:
        kind = "PTRACE";
        snprintf(detail, sizeof(detail), "%s -> pid %u",
                 ptrace_name(e->ptrace.request), e->ptrace.target_pid);
        break;
    case EVT_MPROTECT: {
        char ps[4];
        prot_str(e->mprotect.prot, ps);
        kind = "MPROTECT";
        snprintf(detail, sizeof(detail), "addr=0x%llx len=%llu prot=%s%s",
                 (unsigned long long)e->mprotect.addr,
                 (unsigned long long)e->mprotect.len, ps,
                 ((e->mprotect.prot & 6) == 6) ? "  <-- W+X!" : "");
        break;
    }
    default:
        kind = "OTHER";
        detail[0] = '\0';
    }

    printf("%-8s %-8u %-8u %-6u %-12llu %-16s %s\n", kind, e->pid, e->ppid, e->uid,
           (unsigned long long)e->cgroup_id, e->comm, detail);
    return 0;
}

int main(void)
{
    struct ringbuf_bpf *skel = NULL;
    struct ring_buffer *rb = NULL;
    struct sigaction sa;
    int err = 0;

    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    skel = ringbuf_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "failed to open/load BPF skeleton\n");
        return 1;
    }

    err = ringbuf_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "failed to attach: %d\n", err);
        goto cleanup;
    }

    rb = ring_buffer__new(bpf_map__fd(skel->maps.events), handle_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "failed to create ring buffer\n");
        err = 1;
        goto cleanup;
    }

    printf("%-8s %-8s %-8s %-6s %-12s %-16s %s\n",
           "TYPE", "PID", "PPID", "UID", "CGROUP_ID", "COMM", "DETAIL");

    while (!stop) {
        err = ring_buffer__poll(rb, 100);
        if (err == -EINTR) {
            err = 0;
            break;
        }
        if (err < 0) {
            fprintf(stderr, "poll error: %d\n", err);
            break;
        }
    }

cleanup:
    ring_buffer__free(rb);
    ringbuf_bpf__destroy(skel);
    return err < 0 ? 1 : err;
}
