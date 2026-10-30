"""graph_build.py FILE.jsonl [CONTAINER_NAME] - builds a process graph per window."""
import json, sys, os, collections
import networkx as nx

WINDOW_NS = 10 * 10**9   # 10 s snapshots


def load(path, name=None):
    events = []
    for line in open(path):
        e = json.loads(line)
        if e["type"].startswith("container_"):
            continue
        if name and e.get("name") != name:
            continue
        events.append(e)
    events.sort(key=lambda e: e["ts_ns"])
    return events


def build_graph(events):
    """One graph from a list of events (a window)."""
    g = nx.MultiDiGraph()
    alive = {}                       # pid -> current node id

    def node_for(pid, e=None):
        if pid not in alive:
            nid = "p%d@%d" % (pid, e["ts_ns"] if e else 0)
            alive[pid] = nid
            g.add_node(nid, pid=pid, binary="?", uid=-1, comm="?",
                       n_connect=0, n_mprotect=0, n_ptrace=0, wx=0)
        return alive[pid]

    for e in events:
        t, pid = e["type"], e["pid"]
        if t == "exec":
            # a new program image: fresh node, linked to the parent
            parent = node_for(e["ppid"], e)
            alive.pop(pid, None)
            n = node_for(pid, e)
            g.nodes[n].update(binary=e["filename"], uid=e["uid"], comm=e["comm"])
            g.add_edge(parent, n, rel="spawned", ts=e["ts_ns"])
        elif t == "connect":
            n = node_for(pid, e)
            g.nodes[n]["n_connect"] += 1
            dst = "net:%s:%d" % (e["ip"], e["port"])
            if dst not in g:
                g.add_node(dst, binary="NET", uid=-1, comm="net", n_connect=0,
                           n_mprotect=0, n_ptrace=0, wx=0)
            g.add_edge(n, dst, rel="connected", ts=e["ts_ns"])
        elif t == "mprotect":
            n = node_for(pid, e)
            g.nodes[n]["n_mprotect"] += 1
            if (e["prot"] & 6) == 6:
                g.nodes[n]["wx"] += 1
        elif t == "ptrace":
            n = node_for(pid, e)
            g.nodes[n]["n_ptrace"] += 1
            g.add_edge(n, node_for(e["target_pid"], e), rel="ptraced", ts=e["ts_ns"])
        elif t == "exit":
            alive.pop(pid, None)     # PID may be reused later
    return g


def windows(events, size=WINDOW_NS):
    buckets = collections.defaultdict(list)
    if not events:
        return []
    t0 = events[0]["ts_ns"]
    for e in events:
        buckets[(e["ts_ns"] - t0) // size].append(e)
    return [build_graph(buckets[k]) for k in sorted(buckets)]


if __name__ == "__main__":
    path = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    ev = load(path, name)
    gs = windows(ev)
    print("%s: %d events -> %d windows" % (os.path.basename(path), len(ev), len(gs)))
    for i, g in enumerate(gs[:5]):
        rels = collections.Counter(d["rel"] for _, _, d in g.edges(data=True))
        print("  window %d: %d nodes, %d edges %s" % (i, g.number_of_nodes(),
                                                      g.number_of_edges(), dict(rels)))

