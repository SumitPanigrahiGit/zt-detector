def rep(s, old, new, name):
    assert s.count(old) == 1, name + ": anchor not found: " + old[:60]
    return s.replace(old, new)

l = open("src/loader.c").read()
g = open("ml/graph_build.py").read()
v = open("scripts/verify_all.sh").read()
if "read_image" in l or "13) image" in v:
    raise SystemExit("already patched")

# ---------------- loader ----------------
l = rep(l, "char name[64]; char path[512]; int announced; };",
           "char name[64]; char path[512]; int announced; char image[64]; };", "struct")

l = rep(l, "static void scan_dir(const char *base)", r'''static void read_image(const char *hex, char *out, size_t outsz)
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
    char *q = buf;
    /* the file has "Image" twice: the name (use this) and a sha256 id (skip) */
    while ((q = strstr(q, "\"Image\":\"")) != NULL) {
        q += 9;
        if (strncmp(q, "sha256:", 7) != 0) {
            size_t i = 0;
            while (*q && *q != '"' && i < outsz - 1)
                out[i++] = *q++;
            out[i] = '\0';
            return;
        }
    }
}

static void scan_dir(const char *base)''', "scan_dir")

l = rep(l, "        read_name(hex, ct_cache[ct_count].name, sizeof(ct_cache[ct_count].name));\n",
           "        read_name(hex, ct_cache[ct_count].name, sizeof(ct_cache[ct_count].name));\n"
           "        read_image(hex, ct_cache[ct_count].image, sizeof(ct_cache[ct_count].image));\n", "read_name call")

l = rep(l, "/* ---------- decoding helpers ---------- */", r'''static const char *container_image(unsigned long long cgid)
{
    for (int i = 0; i < ct_count; i++)
        if (ct_cache[i].cgid == cgid)
            return ct_cache[i].image;
    return "-";
}

/* ---------- decoding helpers ---------- */''', "helpers")

l = rep(l, "    json_str(json_fp, container_name(e->cgroup_id));\n",
           "    json_str(json_fp, container_name(e->cgroup_id));\n"
           "    fputs(\",\\\"image\\\":\", json_fp);\n"
           "    json_str(json_fp, container_image(e->cgroup_id));\n", "write_json")

l = rep(l, '        fprintf(json_fp, ",\\"cgroup_id\\":%llu,\\"preexisting\\":%d}\\n", c->cgid, life_initial);',
           '        fputs(",\\"image\\":", json_fp);\n'
           '        json_str(json_fp, c->image);\n'
           '        fprintf(json_fp, ",\\"cgroup_id\\":%llu,\\"preexisting\\":%d}\\n", c->cgid, life_initial);', "emit_life")

# ---------------- graph_build ----------------
g = rep(g, "    start = None\n    pre = False\n", "    start = None\n    pre = False\n    image = None\n", "Events")
g = rep(g, '                events.pre = bool(e.get("preexisting", 0))\n',
           '                events.pre = bool(e.get("preexisting", 0))\n'
           '                events.image = e.get("image")\n', "load")
g = rep(g, "        out.append(gr)\n",
           "        gr.graph['image'] = getattr(events, 'image', None)\n        out.append(gr)\n", "windows")

# ---------------- verify_all.sh: check 13 ----------------
check = r'''echo "== 13) image in events (Day 39) =="
sudo rm -f /tmp/zt_v13.jsonl
docker rm -f zt-img > /dev/null 2>&1
start_loader -q -j /tmp/zt_v13.jsonl
docker run -d --name zt-img nginx:alpine > /dev/null
sleep 1
docker exec zt-img true
sleep 1
docker rm -f zt-img > /dev/null
sleep 1
stop_loader
sudo grep '"type":"container_start"' /tmp/zt_v13.jsonl | grep -q '"image":"nginx:alpine"' \
  && sudo grep '"type":"exec"' /tmp/zt_v13.jsonl | grep -q '"image":"nginx:alpine"' \
  && pass "image recorded in lifecycle and exec events" || fail "image missing"

'''
v = rep(v, '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', check + '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"', "verify")

open("src/loader.c", "w").write(l)
open("ml/graph_build.py", "w").write(g)
open("scripts/verify_all.sh", "w").write(v)
print("patched")
