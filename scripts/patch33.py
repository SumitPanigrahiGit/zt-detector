p = "ml/encode.py"
s = open(p).read()
if "win_exec" in s:
    raise SystemExit("already patched")

def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not found: " + old[:60]
    s = s.replace(old, new)

# 1) wider feature matrix + window-level counts computed from the graph
rep("    x = torch.zeros(len(nodes), V + 6)\n",
    "    # window-level rate features (same value on every node of the window)\n"
    "    win_exec = sum(1 for _, _, d in g.edges(data=True) if d['rel'] == 'spawned')\n"
    "    win_procs = sum(1 for n in nodes if g.nodes[n]['binary'] != 'NET')\n"
    "    win_conn = sum(1 for _, _, d in g.edges(data=True) if d['rel'] == 'connected')\n"
    "    x = torch.zeros(len(nodes), V + 9)\n")
rep("        x[i, V + 5] = 1.0 if a[\"wx\"] > 0 else 0.0\n",
    "        x[i, V + 5] = 1.0 if a[\"wx\"] > 0 else 0.0\n"
    "        x[i, V + 6] = math.log1p(win_exec)\n"
    "        x[i, V + 7] = math.log1p(win_procs)\n"
    "        x[i, V + 8] = math.log1p(win_conn)\n")

# 2) sanity checks in __main__ use the new width
rep("assert d.x.shape[1] == len(vocab) + 7", "assert d.x.shape[1] == len(vocab) + 10")
rep("int(d.x[:, len(vocab) + 6].sum().item())", "int(d.x[:, len(vocab) + 6].sum().item())")
rep('print("vocab size:", len(vocab), "feature dim:", len(vocab) + 7)',
    'print("vocab size:", len(vocab), "feature dim:", len(vocab) + 10)')

open(p, "w").write(s)
print("patched")
