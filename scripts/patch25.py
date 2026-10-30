def rep(s, old, new, path):
    assert s.count(old) == 1, path + ": anchor not found: " + old[:60]
    return s.replace(old, new)

l = open("src/loader.c").read()
v = open("scripts/verify_all.sh").read()
if "lat_us" in l or "9) latency" in v:
    raise SystemExit("already patched")

l = rep(l, "/* ---------- in-kernel host filter ---------- */", r'''/* ---------- kernel -> user-space latency ---------- */
#define MAX_LAT 200000
static unsigned int lat_us[MAX_LAT];
static size_t lat_n = 0;

static int cmp_u32(const void *a, const void *b)
{
    unsigned int x = *(const unsigned int *)a, y = *(const unsigned int *)b;
    return (x > y) - (x < y);
}

static void record_latency(unsigned long long kernel_ts_ns)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    unsigned long long now = ts.tv_sec * 1000000000ULL + ts.tv_nsec;
    if (now < kernel_ts_ns || lat_n >= MAX_LAT)
        return;
    unsigned long long us = (now - kernel_ts_ns) / 1000;
    lat_us[lat_n++] = us > 0xffffffffULL ? 0xffffffffU : (unsigned int)us;
}

static void print_latency(void)
{
    if (lat_n == 0) {
        printf("latency kernel->user (us): n=0\n");
        return;
    }
    qsort(lat_us, lat_n, sizeof(lat_us[0]), cmp_u32);
    printf("latency kernel->user (us): n=%zu p50=%u p99=%u max=%u\n",
           lat_n, lat_us[lat_n / 2], lat_us[(lat_n * 99) / 100], lat_us[lat_n - 1]);
}

/* ---------- in-kernel host filter ---------- */''', "loader")

l = rep(l, "    const char *cid = container_of(e->cgroup_id);\n",
           "    record_latency(e->ts_ns);   /* measure before any other work */\n"
           "    const char *cid = container_of(e->cgroup_id);\n", "loader")
l = rep(l, "    print_drops();\n    print_filtered();\n",
           "    print_drops();\n    print_filtered();\n    print_latency();\n", "loader")

check = r'''echo "== 9) latency (Day 25) =="
start_loader -q
for i in $(seq 200); do /bin/true; sleep 0.01; done
sleep 1
stop_loader
LN=$(sed -n 's/^latency.*n=\([0-9]*\).*/\1/p' /tmp/zt_v_out.txt | head -1)
LP=$(sed -n 's/^latency.*p99=\([0-9]*\).*/\1/p' /tmp/zt_v_out.txt | head -1)
LM=$(sed -n 's/^latency.*p50=\([0-9]*\).*/\1/p' /tmp/zt_v_out.txt | head -1)
[ "${LN:-0}" -gt 100 ] && [ "${LP:-999999999}" -lt 100000 ] \
  && pass "latency measured (n=$LN p50=${LM}us p99=${LP}us)" \
  || fail "latency check (n='$LN' p99='$LP')"

'''
v = rep(v, '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', check + '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', "verify_all.sh")

open("src/loader.c", "w").write(l)
open("scripts/verify_all.sh", "w").write(v)
print("patched")
