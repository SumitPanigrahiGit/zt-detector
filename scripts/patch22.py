def load(path):
    return open(path).read()

def rep(s, old, new, path):
    assert s.count(old) == 1, path + ": anchor not found: " + old[:60]
    return s.replace(old, new)

# check everything is unpatched first, so the patch is all-or-nothing
for path, marker in [("bpf/common.h", "EVT_EXIT"), ("bpf/ringbuf.bpf.c", "sched_process_exit"),
                     ("src/loader.c", "EVT_EXIT"), ("scripts/verify_all.sh", "6) process exit")]:
    if marker in load(path):
        raise SystemExit(path + ": already patched")

# ---- common.h ----
s = load("bpf/common.h")
s = rep(s, "    EVT_MPROTECT = 4,   // Day 10\n",
        "    EVT_MPROTECT = 4,   // Day 10\n    EVT_EXIT     = 5,   // Day 22\n", "common.h")
s = rep(s, "struct { __u64 addr; __u64 len; __u32 prot; __u32 _pad; } mprotect;",
        "struct { __u64 addr; __u64 len; __u32 prot; __u32 _pad; } mprotect;\n"
        "        struct { __u32 exit_code; __u32 _pad; } exit;   // raw: (status << 8) | signal", "common.h")
new_common = s

# ---- eBPF program ----
b = load("bpf/ringbuf.bpf.c")
b += r'''
SEC("tracepoint/sched/sched_process_exit")
int trace_exit(void *ctx)
{
    __u64 id = bpf_get_current_pid_tgid();

    // Fires for every thread. Only report when the thread group leader
    // exits (tid == tgid), i.e. the whole process is ending.
    if ((__u32)id != (__u32)(id >> 32))
        return 0;

    struct task_struct *task = (struct task_struct *)bpf_get_current_task();

    struct event *e = new_event(EVT_EXIT);
    if (!e)
        return 0;

    e->exit.exit_code = (__u32)BPF_CORE_READ(task, exit_code);
    e->exit._pad = 0;

    bpf_ringbuf_submit(e, 0);
    return 0;
}
'''
new_bpf = b

# ---- loader ----
l = load("src/loader.c")
l = rep(l, '"other", "exec", "connect", "ptrace", "mprotect" };',
           '"other", "exec", "connect", "ptrace", "mprotect", "exit" };', "loader")
l = rep(l, "(e->type >= 1 && e->type <= 4) ? tn[e->type]",
           "(e->type >= 1 && e->type <= 5) ? tn[e->type]", "loader")
l = rep(l, "    case EVT_MPROTECT:\n        fprintf(json_fp",
    "    case EVT_EXIT:\n"
    "        fprintf(json_fp, \",\\\"exit_code\\\":%u,\\\"signal\\\":%u\",\n"
    "                e->exit.exit_code >> 8, e->exit.exit_code & 0x7f);\n"
    "        break;\n"
    "    case EVT_MPROTECT:\n        fprintf(json_fp", "loader")
l = rep(l, "    case EVT_MPROTECT: {",
    "    case EVT_EXIT:\n"
    "        kind = \"EXIT\";\n"
    "        snprintf(detail, sizeof(detail), \"code=%u signal=%u\",\n"
    "                 e->exit.exit_code >> 8, e->exit.exit_code & 0x7f);\n"
    "        break;\n"
    "    case EVT_MPROTECT: {", "loader")
new_loader = l

# ---- add a check to verify_all.sh ----
v = load("scripts/verify_all.sh")
check = r'''echo "== 6) process exit (Day 22) =="
sudo rm -f /tmp/zt_v6.jsonl
start_loader -q -j /tmp/zt_v6.jsonl
sh -c 'exit 3'
sleep 1
stop_loader
sudo grep '"type":"exit"' /tmp/zt_v6.jsonl | grep -q '"exit_code":3' \
  && pass "exit code 3 captured" || fail "no exit event with code 3"

'''
v = rep(v, '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', check + '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', "verify_all.sh")

# write everything only after all edits succeeded
open("bpf/common.h", "w").write(new_common)
open("bpf/ringbuf.bpf.c", "w").write(new_bpf)
open("src/loader.c", "w").write(new_loader)
open("scripts/verify_all.sh", "w").write(v)
print("patched")
