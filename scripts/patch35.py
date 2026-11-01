def rep(s, old, new, name):
    assert s.count(old) == 1, name + ": anchor not found: " + old[:60]
    return s.replace(old, new)

g = open("ml/graph_build.py").read()
e = open("ml/encode.py").read()
if "startup" in g or "is_startup" in e:
    raise SystemExit("already patched")

# graph_build: tag each window graph with its index within the recording
g = rep(g, "    return [build_graph(buckets[k]) for k in sorted(buckets)]",
        "    out = []\n"
        "    for i, k in enumerate(sorted(buckets)):\n"
        "        gr = build_graph(buckets[k])\n"
        "        gr.graph['startup'] = 1 if i == 0 else 0   # first window of the container's recording\n"
        "        out.append(gr)\n"
        "    return out", "graph_build")

# encode: one extra column
e = rep(e, "x = torch.zeros(len(nodes), V + 9)", "x = torch.zeros(len(nodes), V + 10)", "encode")
e = rep(e, "        x[i, V + 8] = math.log1p(win_conn)\n",
        "        x[i, V + 8] = math.log1p(win_conn)\n"
        "        x[i, V + 9] = float(g.graph.get('startup', 0))\n", "encode")
e = rep(e, "assert d.x.shape[1] == len(vocab) + 10", "assert d.x.shape[1] == len(vocab) + 11", "encode")
e = rep(e, 'print("vocab size:", len(vocab), "feature dim:", len(vocab) + 10)',
        'print("vocab size:", len(vocab), "feature dim:", len(vocab) + 11)', "encode")
open("ml/graph_build.py", "w").write(g)
open("ml/encode.py", "w").write(e)
print("patched")
