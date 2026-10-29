s = open("src/loader.c").read()
if "write_json" in s:
    raise SystemExit("already patched")

def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not found: " + old[:50]
    s = s.replace(old, new)

# 1) JSON writer, placed just before handle_event
rep("static int handle_event(void *ctx, void *data, size_t size)", r'''/* ---------- JSON Lines output (-j FILE) ---------- */
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
    static const char *tn[] = { "other", "exec", "connect", "ptrace", "mprotect" };
    if (!json_fp)
        return;
    const char *t = (e->type >= 1 && e->type <= 4) ? tn[e->type] : tn[0];

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
    case EVT_MPROTECT:
        fprintf(json_fp, ",\"addr\":%llu,\"len\":%llu,\"prot\":%u",
                (unsigned long long)e->mprotect.addr,
                (unsigned long long)e->mprotect.len, e->mprotect.prot);
        break;
    }
    fputs("}\n", json_fp);
}

static int handle_event(void *ctx, void *data, size_t size)''')

# 2) write each event after the -c filter, before the -q early return
rep("    record_stat(e, cid);\n    if (quiet)",
    "    record_stat(e, cid);\n    write_json(e, cid);\n    if (quiet)")

# 3) parse -j FILE
rep("            quiet = 1;\n",
    "            quiet = 1;\n"
    "        else if (strcmp(argv[i], \"-j\") == 0 && i + 1 < argc)\n"
    "            json_path = argv[++i];\n")

# 4) open the file before installing signal handlers
rep("    memset(&sa, 0, sizeof(sa));",
    "    if (json_path) {\n"
    "        json_fp = fopen(json_path, \"w\");\n"
    "        if (!json_fp) {\n"
    "            perror(\"fopen json\");\n"
    "            return 1;\n"
    "        }\n"
    "        setvbuf(json_fp, NULL, _IOLBF, 0);   /* line buffered: tail -f works */\n"
    "    }\n\n"
    "    memset(&sa, 0, sizeof(sa));")

# 5) close the file at exit
rep("    print_drops();\n\ncleanup:\n",
    "    print_drops();\n    if (json_fp)\n        fclose(json_fp);\n\ncleanup:\n")

open("src/loader.c", "w").write(s)
print("patched")
