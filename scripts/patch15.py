p = "src/loader.c"
s = open(p).read()
if "record_stat" in s:
    raise SystemExit("already patched")

def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not found: " + old[:40]
    s = s.replace(old, new)

rep("static int handle_event(void *ctx, void *data, size_t size)", r'''/* ---------- per-container event counters ---------- */
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

static int handle_event(void *ctx, void *data, size_t size)''')

rep(r'''    if (only_containers && strcmp(cid, "host") == 0)
        return 0;
''', r'''    if (only_containers && strcmp(cid, "host") == 0)
        return 0;

    record_stat(e, cid);
    if (quiet)
        return 0;
''')

rep("            only_containers = 1;\n",
    '            only_containers = 1;\n'
    '        else if (strcmp(argv[i], "-q") == 0)\n'
    '            quiet = 1;\n')

rep("cleanup:\n    ring_buffer__free(rb);",
    "    print_stats();\n\ncleanup:\n    ring_buffer__free(rb);")

open(p, "w").write(s)
print("patched")