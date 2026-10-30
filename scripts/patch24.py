def rep(s, old, new, path):
    assert s.count(old) == 1, path + ": anchor not found: " + old[:60]
    return s.replace(old, new)

b = open("bpf/ringbuf.bpf.c").read()
l = open("src/loader.c").read()
v = open("scripts/verify_all.sh").read()
if "host_cgroups" in b or "8) in-kernel" in v:
    raise SystemExit("already patched")

# ---------------- eBPF side ----------------
b = rep(b, "// Reserve an event and fill the fields common to every syscall.", r'''// Cgroups that user space has confirmed are NOT containers.
// Fail-open: unknown cgroups are still reported.
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u64);
    __type(value, __u8);
} host_cgroups SEC(".maps");

// Events dropped in the kernel by the host filter (not a loss: intended).
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} filtered SEC(".maps");

// Set by user space after load (loader -c).
volatile __u32 filter_enabled = 0;

// Reserve an event and fill the fields common to every syscall.''', "bpf")

b = rep(b, "static __always_inline struct event *new_event(__u32 type)\n{\n", r'''static __always_inline struct event *new_event(__u32 type)
{
    if (filter_enabled) {
        __u64 cg = bpf_get_current_cgroup_id();
        if (bpf_map_lookup_elem(&host_cgroups, &cg)) {
            __u32 fk = 0;
            __u64 *fn = bpf_map_lookup_elem(&filtered, &fk);
            if (fn)
                (*fn)++;
            return NULL;   // known host cgroup: skip before touching the ring buffer
        }
    }
''', "bpf")

# ---------------- loader ----------------
l = rep(l, "/* ---------- container lifetime events ---------- */", r'''/* ---------- in-kernel host filter ---------- */
static int host_fd = -1;
static int filtered_fd = -1;
static unsigned long long cand[256];   /* cgroups seen as "host", not yet confirmed */
static int cand_n = 0;

static void note_host(unsigned long long cg)
{
    for (int i = 0; i < cand_n; i++)
        if (cand[i] == cg)
            return;
    if (cand_n < 256)
        cand[cand_n++] = cg;
}

static void host_forget(unsigned long long cg)
{
    if (host_fd >= 0)
        bpf_map_delete_elem(host_fd, &cg);
}

/* Called right after a fresh cgroup scan: a candidate that is still not a
 * container is confirmed host and handed to the kernel filter. */
static void promote_hosts(void)
{
    __u8 one = 1;
    for (int i = 0; i < cand_n; i++) {
        int is_ct = 0;
        for (int j = 0; j < ct_count; j++)
            if (ct_cache[j].cgid == cand[i])
                is_ct = 1;
        if (!is_ct && host_fd >= 0)
            bpf_map_update_elem(host_fd, &cand[i], &one, BPF_ANY);
    }
    cand_n = 0;
}

static void print_filtered(void)
{
    int ncpu = libbpf_num_possible_cpus();
    if (filtered_fd < 0 || ncpu <= 0)
        return;
    __u64 *vals = calloc(ncpu, sizeof(__u64));
    if (!vals)
        return;
    __u32 key = 0;
    unsigned long long total = 0;
    if (bpf_map_lookup_elem(filtered_fd, &key, vals) == 0)
        for (int i = 0; i < ncpu; i++)
            total += vals[i];
    free(vals);
    printf("filtered in kernel (host events): %llu\n", total);
}

/* ---------- container lifetime events ---------- */''', "loader")

l = rep(l, "            ct_cache[i].announced = 1;\n",
           "            ct_cache[i].announced = 1;\n            host_forget(ct_cache[i].cgid);\n", "loader")
l = rep(l, "    life_initial = 0;\n    first = 0;\n}",
           "    life_initial = 0;\n    first = 0;\n    promote_hosts();\n}", "loader")
l = rep(l, '    if (only_containers && strcmp(cid, "host") == 0)\n        return 0;\n',
           '    if (only_containers && strcmp(cid, "host") == 0) {\n        note_host(e->cgroup_id);\n        return 0;\n    }\n', "loader")
l = rep(l, "    drops_fd = bpf_map__fd(skel->maps.drops);\n",
           "    drops_fd = bpf_map__fd(skel->maps.drops);\n"
           "    host_fd = bpf_map__fd(skel->maps.host_cgroups);\n"
           "    filtered_fd = bpf_map__fd(skel->maps.filtered);\n"
           "    skel->bss->filter_enabled = only_containers ? 1 : 0;\n", "loader")
l = rep(l, "    print_drops();\n", "    print_drops();\n    print_filtered();\n", "loader")

# ---------------- verify_all.sh: check 8 ----------------
check = r'''echo "== 8) in-kernel container filter (Day 24) =="
sudo setsid ./build/loader -q -c > /tmp/zt_v_out.txt 2>&1 < /dev/null &
sleep 2
for i in 1 2 3; do /bin/true; done
sleep 1
LP=$(pgrep -x loader | tail -1)
sudo kill -STOP "$LP"
( for i in $(seq 3000); do /bin/true; done ) < /dev/null
sudo kill -CONT "$LP"
sleep 2
stop_loader
D8=$(grep "dropped events" /tmp/zt_v_out.txt | awk '{print $NF}')
F8=$(grep "filtered in kernel" /tmp/zt_v_out.txt | awk '{print $NF}')
[ "${D8:-999}" -lt 50 ] && [ "${F8:-0}" -gt 2000 ] \
  && pass "host events filtered in kernel (filtered=$F8, dropped=$D8)" \
  || fail "filter not effective (filtered='$F8', dropped='$D8')"

'''
v = rep(v, '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', check + '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', "verify_all.sh")

open("bpf/ringbuf.bpf.c", "w").write(b)
open("src/loader.c", "w").write(l)
open("scripts/verify_all.sh", "w").write(v)
print("patched")
