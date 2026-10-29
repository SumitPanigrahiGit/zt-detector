def patch(path, edits):
    s = open(path).read()
    if "drops" in s:
        raise SystemExit(path + ": already patched")
    for old, new in edits:
        assert s.count(old) == 1, path + ": anchor not found: " + old[:50]
        s = s.replace(old, new)
    open(path, "w").write(s)

# ---------- eBPF side ----------
patch("bpf/ringbuf.bpf.c", [
    ("// Reserve an event and fill the fields common to every syscall.",
     r'''// Counts events lost because the ring buffer was full.
// Per-CPU: each CPU increments its own slot, so no locking is needed.
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} drops SEC(".maps");

// Reserve an event and fill the fields common to every syscall.'''),
    ("    if (!e)\n        return NULL;   // buffer full: drop, never block the kernel\n",
     r'''    if (!e) {
        // Buffer full: count the loss, never block the kernel.
        __u32 k = 0;
        __u64 *cnt = bpf_map_lookup_elem(&drops, &k);
        if (cnt)
            (*cnt)++;
        return NULL;
    }
'''),
])

# ---------- user-space side ----------
patch("src/loader.c", [
    ("#include <stdio.h>\n", "#include <stdio.h>\n#include <stdlib.h>\n"),
    ("#include <bpf/libbpf.h>\n", "#include <bpf/libbpf.h>\n#include <bpf/bpf.h>\n"),
    ("static int handle_event(void *ctx, void *data, size_t size)",
     r'''/* ---------- dropped-event counter ---------- */
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

static int handle_event(void *ctx, void *data, size_t size)'''),
    ("    err = ringbuf_bpf__attach(skel);\n",
     "    drops_fd = bpf_map__fd(skel->maps.drops);\n    err = ringbuf_bpf__attach(skel);\n"),
    ("    print_stats();\n\ncleanup:\n",
     "    print_stats();\n    print_drops();\n\ncleanup:\n"),
])

print("patched")
