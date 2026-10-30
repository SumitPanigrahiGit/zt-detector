def rep(s, old, new, path):
    assert s.count(old) == 1, path + ": anchor not found: " + old[:60]
    return s.replace(old, new)

l = open("src/loader.c").read()
v = open("scripts/verify_all.sh").read()
if "lifecycle_tick" in l or "7) container start/stop" in v:
    raise SystemExit("already patched")

# ---- loader ----
l = rep(l, "char name[64]; char path[512]; };",
           "char name[64]; char path[512]; int announced; };", "loader")
l = rep(l, "        ct_cache[ct_count].cgid = st.st_ino;\n",
           "        ct_cache[ct_count].cgid = st.st_ino;\n        ct_cache[ct_count].announced = 0;\n", "loader")
l = rep(l, "static void prune_cache(void)",
           "static void emit_life(const char *kind, const struct ct_entry *c);\n\nstatic void prune_cache(void)", "loader")
l = rep(l, "            ct_cache[j++] = ct_cache[i];\n",
           "            ct_cache[j++] = ct_cache[i];\n"
           "        else if (ct_cache[i].announced)\n"
           "            emit_life(\"stop\", &ct_cache[i]);\n", "loader")

l = rep(l, "static int handle_event(void *ctx, void *data, size_t size)", r'''/* ---------- container lifetime events ---------- */
static int life_initial = 0;   /* 1 while announcing containers that already existed */

static void emit_life(const char *kind, const struct ct_entry *c)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);   /* same time base as bpf_ktime_get_ns() */
    unsigned long long ns = ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    if (json_fp) {
        fprintf(json_fp, "{\"ts_ns\":%llu,\"type\":\"container_%s\",\"container\":", ns, kind);
        json_str(json_fp, c->id);
        fputs(",\"name\":", json_fp);
        json_str(json_fp, c->name);
        fprintf(json_fp, ",\"cgroup_id\":%llu,\"preexisting\":%d}\n", c->cgid, life_initial);
    }
    if (!quiet)
        printf("%-8s %-8s %-8s %-6s %-13s %-16s %-16s %s\n", "LIFE", "-", "-", "-",
               c->id, c->name, "-", kind);
}

/* Called from the poll loop; does real work at most every 100 ms. */
static void lifecycle_tick(void)
{
    static long long last = -1000;
    static int first = 1;
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    long long now = ts.tv_sec * 1000LL + ts.tv_nsec / 1000000;
    if (now - last < 100)
        return;
    last = now;

    prune_cache();                               /* emits "stop" for vanished containers */
    scan_dir("/sys/fs/cgroup/system.slice");
    scan_dir("/sys/fs/cgroup/docker");

    life_initial = first;
    for (int i = 0; i < ct_count; i++) {
        if (!ct_cache[i].announced) {
            ct_cache[i].announced = 1;
            emit_life("start", &ct_cache[i]);
        }
    }
    life_initial = 0;
    first = 0;
}

static int handle_event(void *ctx, void *data, size_t size)''', "loader")

l = rep(l, "        err = ring_buffer__poll(rb, 100);\n",
           "        lifecycle_tick();\n        err = ring_buffer__poll(rb, 100);\n", "loader")

# ---- verify_all.sh: check 7 ----
check = r'''echo "== 7) container start/stop (Day 23) =="
sudo rm -f /tmp/zt_v7.jsonl
docker rm -f zt-life > /dev/null 2>&1
start_loader -q -j /tmp/zt_v7.jsonl
docker run -d --name zt-life alpine sleep 600 > /dev/null
sleep 1
docker rm -f zt-life > /dev/null
sleep 1
stop_loader
sudo grep -E '"type":"container_start".*"name":"zt-life"' /tmp/zt_v7.jsonl | grep -q '"preexisting":0' && S1=1 || S1=0
sudo grep -E '"type":"container_stop".*"name":"zt-life"' /tmp/zt_v7.jsonl | grep -q . && S2=1 || S2=0
[ "$S1" = 1 ] && [ "$S2" = 1 ] && pass "container start and stop recorded with name" || fail "start=$S1 stop=$S2"

'''
v = rep(v, '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', check + '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', "verify_all.sh")

open("src/loader.c", "w").write(l)
open("scripts/verify_all.sh", "w").write(v)
print("patched")
