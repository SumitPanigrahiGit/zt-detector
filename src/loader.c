// loader.c - prints kernel events with the Docker container ID resolved
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <dirent.h>
#include <ctype.h>
#include <sys/stat.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <linux/types.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "common.h"
#include "ringbuf.skel.h"

static volatile sig_atomic_t stop = 0;
static void on_signal(int sig) { (void)sig; stop = 1; }

/* ---------- cgroup ID -> container ID cache ---------- */
#define MAX_CT 256
struct ct_entry { unsigned long long cgid; char id[13]; char name[64]; char path[512]; };
static struct ct_entry ct_cache[MAX_CT];
static int ct_count = 0;
static long long last_scan = 0;   /* ms, CLOCK_MONOTONIC */
static int only_containers = 0;   /* -c flag */

static int is_hex64(const char *s)
{
    if (strlen(s) != 64)
        return 0;
    for (int i = 0; i < 64; i++)
        if (!isxdigit((unsigned char)s[i]))
            return 0;
    return 1;
}

static void read_name(const char *hex, char *out, size_t outsz)
{
    static char buf[32768];
    char path[256];
    snprintf(path, sizeof(path),
             "/var/lib/docker/containers/%.64s/config.v2.json", hex);
    snprintf(out, outsz, "?");
    FILE *f = fopen(path, "r");
    if (!f)
        return;
    size_t n = fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    buf[n] = '\0';
    char *q = strstr(buf, "\"Name\":\"/");
    if (!q)
        return;
    q += 9;
    size_t i = 0;
    while (*q && *q != '"' && i < outsz - 1)
        out[i++] = *q++;
    out[i] = '\0';
}

static void scan_dir(const char *base)
{
    DIR *d = opendir(base);
    if (!d)
        return;
    struct dirent *de;
    while ((de = readdir(d)) != NULL) {
        const char *hex = NULL;
        size_t n = strlen(de->d_name);

        if (strncmp(de->d_name, "docker-", 7) == 0 && n == 7 + 64 + 6 &&
            strcmp(de->d_name + n - 6, ".scope") == 0)
            hex = de->d_name + 7;              /* systemd cgroup driver */
        else if (is_hex64(de->d_name))
            hex = de->d_name;                  /* cgroupfs driver */
        if (!hex)
            continue;

        char path[512];
        struct stat st;
        snprintf(path, sizeof(path), "%s/%s", base, de->d_name);
        if (stat(path, &st) != 0)
            continue;

        int known = 0;
        for (int i = 0; i < ct_count; i++)
            if (ct_cache[i].cgid == (unsigned long long)st.st_ino)
                known = 1;
        if (known || ct_count >= MAX_CT)
            continue;

        ct_cache[ct_count].cgid = st.st_ino;
        snprintf(ct_cache[ct_count].path, sizeof(ct_cache[ct_count].path), "%s", path);
        memcpy(ct_cache[ct_count].id, hex, 12);
        ct_cache[ct_count].id[12] = '\0';
        read_name(hex, ct_cache[ct_count].name, sizeof(ct_cache[ct_count].name));
        ct_count++;
    }
    closedir(d);
}

/* Drop entries whose cgroup directory was removed or whose inode changed. */
static void prune_cache(void)
{
    int j = 0;
    for (int i = 0; i < ct_count; i++) {
        struct stat st;
        if (stat(ct_cache[i].path, &st) == 0 &&
            (unsigned long long)st.st_ino == ct_cache[i].cgid)
            ct_cache[j++] = ct_cache[i];
    }
    ct_count = j;
}

/* Returns the 12-char container ID, or "host" if the cgroup is not a container. */
static const char *container_of(unsigned long long cgid)
{
    for (int pass = 0; pass < 2; pass++) {
        for (int i = 0; i < ct_count; i++)
            if (ct_cache[i].cgid == cgid)
                return ct_cache[i].id;
        struct timespec ts;
        clock_gettime(CLOCK_MONOTONIC, &ts);
        long long now = ts.tv_sec * 1000LL + ts.tv_nsec / 1000000;
        if (pass == 0 && now - last_scan >= 20) {   /* rescan at most once per second */
            last_scan = now;
            prune_cache();
            scan_dir("/sys/fs/cgroup/system.slice");
            scan_dir("/sys/fs/cgroup/docker");
        } else {
            break;
        }
    }
    return "host";
}

static const char *container_name(unsigned long long cgid)
{
    for (int i = 0; i < ct_count; i++)
        if (ct_cache[i].cgid == cgid)
            return ct_cache[i].name;
    return "-";
}

/* ---------- decoding helpers ---------- */
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

/* ---------- per-container event counters ---------- */
#define MAX_STATS 256
struct stat_entry {
    unsigned long long cgid;
    char id[13];
    char name[64];
    unsigned long long count[5];   /* index = event type (1..4) */
};
static struct stat_entry stats[MAX_STATS];
static int stat_count = 0;
static int quiet = 0;              /* -q flag */

static void record_stat(const struct event *e, const char *cid)
{
    if (e->type < 1 || e->type > 4)
        return;
    for (int i = 0; i < stat_count; i++) {
        if (stats[i].cgid == e->cgroup_id) {
            stats[i].count[e->type]++;
            return;
        }
    }
    if (stat_count >= MAX_STATS)
        return;                    /* table full: ignore new groups */
    struct stat_entry *st = &stats[stat_count++];
    st->cgid = e->cgroup_id;
    snprintf(st->id, sizeof(st->id), "%s", cid);
    snprintf(st->name, sizeof(st->name), "%s", container_name(e->cgroup_id));
    st->count[e->type] = 1;
}

static void print_stats(void)
{
    printf("\n%-13s %-16s %8s %8s %8s %8s\n",
           "CONTAINER", "NAME", "EXEC", "CONNECT", "PTRACE", "MPROTECT");
    for (int i = 0; i < stat_count; i++)
        printf("%-13s %-16s %8llu %8llu %8llu %8llu\n",
               stats[i].id, stats[i].name,
               stats[i].count[1], stats[i].count[2],
               stats[i].count[3], stats[i].count[4]);
}

/* ---------- dropped-event counter ---------- */
static int drops_fd = -1;

static void print_drops(void)
{
    int ncpu = libbpf_num_possible_cpus();
    if (drops_fd < 0 || ncpu <= 0)
        return;
    __u64 *vals = calloc(ncpu, sizeof(__u64));
    if (!vals)
        return;
    __u32 key = 0;
    unsigned long long total = 0;
    if (bpf_map_lookup_elem(drops_fd, &key, vals) == 0)
        for (int i = 0; i < ncpu; i++)
            total += vals[i];
    free(vals);
    printf("\ndropped events (ring buffer full): %llu\n", total);
}

/* ---------- JSON Lines output (-j FILE) ---------- */
static FILE *json_fp = NULL;
static const char *json_path = NULL;

static void json_str(FILE *f, const char *s)
{
    fputc('"', f);
    for (; *s; s++) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') {
            fputc('\\', f);
            fputc(c, f);
        } else if (c < 0x20) {
            fprintf(f, "\\u%04x", c);
        } else {
            fputc(c, f);
        }
    }
    fputc('"', f);
}

static void write_json(const struct event *e, const char *cid)
{
    static const char *tn[] = { "other", "exec", "connect", "ptrace", "mprotect", "exit" };
    if (!json_fp)
        return;
    const char *t = (e->type >= 1 && e->type <= 5) ? tn[e->type] : tn[0];

    fprintf(json_fp, "{\"ts_ns\":%llu,\"type\":\"%s\",\"pid\":%u,\"ppid\":%u,\"uid\":%u,\"container\":",
            (unsigned long long)e->ts_ns, t, e->pid, e->ppid, e->uid);
    json_str(json_fp, cid);
    fputs(",\"name\":", json_fp);
    json_str(json_fp, container_name(e->cgroup_id));
    fputs(",\"comm\":", json_fp);
    json_str(json_fp, e->comm);

    switch (e->type) {
    case EVT_EXEC:
        fputs(",\"filename\":", json_fp);
        json_str(json_fp, e->exec.filename);
        break;
    case EVT_CONNECT: {
        char ip[INET6_ADDRSTRLEN];
        if (e->connect.family == 10) {
            inet_ntop(AF_INET6, e->connect.daddr6, ip, sizeof(ip));
        } else {
            struct in_addr a = { .s_addr = e->connect.daddr };
            inet_ntop(AF_INET, &a, ip, sizeof(ip));
        }
        fprintf(json_fp, ",\"family\":%u,\"ip\":\"%s\",\"port\":%u",
                e->connect.family, ip, ntohs(e->connect.dport));
        break;
    }
    case EVT_PTRACE:
        fprintf(json_fp, ",\"request\":%u,\"request_name\":\"%s\",\"target_pid\":%u",
                e->ptrace.request, ptrace_name(e->ptrace.request), e->ptrace.target_pid);
        break;
    case EVT_EXIT:
        fprintf(json_fp, ",\"exit_code\":%u,\"signal\":%u",
                e->exit.exit_code >> 8, e->exit.exit_code & 0x7f);
        break;
    case EVT_MPROTECT:
        fprintf(json_fp, ",\"addr\":%llu,\"len\":%llu,\"prot\":%u",
                (unsigned long long)e->mprotect.addr,
                (unsigned long long)e->mprotect.len, e->mprotect.prot);
        break;
    }
    fputs("}\n", json_fp);
}

static int handle_event(void *ctx, void *data, size_t size)
{
    const struct event *e = data;
    const char *kind;
    char detail[160];

    if (size < sizeof(*e))
        return 0;

    const char *cid = container_of(e->cgroup_id);
    if (only_containers && strcmp(cid, "host") == 0)
        return 0;

    record_stat(e, cid);
    write_json(e, cid);
    if (quiet)
        return 0;

    switch (e->type) {
    case EVT_EXEC:
        kind = "EXEC";
        snprintf(detail, sizeof(detail), "%s", e->exec.filename);
        break;
    case EVT_CONNECT: {
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
    case EVT_PTRACE:
        kind = "PTRACE";
        snprintf(detail, sizeof(detail), "%s -> pid %u",
                 ptrace_name(e->ptrace.request), e->ptrace.target_pid);
        break;
    case EVT_EXIT:
        kind = "EXIT";
        snprintf(detail, sizeof(detail), "code=%u signal=%u",
                 e->exit.exit_code >> 8, e->exit.exit_code & 0x7f);
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

    printf("%-8s %-8u %-8u %-6u %-13s %-16s %-16s %s\n", kind, e->pid, e->ppid,
           e->uid, cid, container_name(e->cgroup_id), e->comm, detail);
    return 0;
}

int main(int argc, char **argv)
{
    struct ringbuf_bpf *skel = NULL;
    struct ring_buffer *rb = NULL;
    struct sigaction sa;
    int err = 0;

    for (int i = 1; i < argc; i++)
        if (strcmp(argv[i], "-c") == 0)
            only_containers = 1;
        else if (strcmp(argv[i], "-q") == 0)
            quiet = 1;
        else if (strcmp(argv[i], "-j") == 0 && i + 1 < argc)
            json_path = argv[++i];

    if (json_path) {
        json_fp = fopen(json_path, "w");
        if (!json_fp) {
            perror("fopen json");
            return 1;
        }
        setvbuf(json_fp, NULL, _IOLBF, 0);   /* line buffered: tail -f works */
    }

    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    skel = ringbuf_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "failed to open/load BPF skeleton\n");
        return 1;
    }

    drops_fd = bpf_map__fd(skel->maps.drops);
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

    printf("%-8s %-8s %-8s %-6s %-13s %-16s %-16s %s\n",
           "TYPE", "PID", "PPID", "UID", "CONTAINER", "NAME", "COMM", "DETAIL");

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

    print_stats();
    print_drops();
    if (json_fp)
        fclose(json_fp);

cleanup:
    ring_buffer__free(rb);
    ringbuf_bpf__destroy(skel);
    return err < 0 ? 1 : err;
}
