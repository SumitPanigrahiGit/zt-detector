"""encode.py - turns window graphs into PyTorch Geometric Data objects.
Run from the project root: python3 ml/encode.py"""
import os, math, json, collections
import torch
from torch_geometric.data import Data
from graph_build import load, windows

REL = {"spawned": 0, "connected": 1, "ptraced": 2}

SETS = {
    "train":  [("data/normal_train.jsonl", "zt-proxy"), ("data/normal_train.jsonl", "zt-backend")],
    "val":    [("data/normal_val.jsonl", "zt-proxy"), ("data/normal_val.jsonl", "zt-backend")],
    "attack": [("data/attack_demo.jsonl", "zt-victim")],
}


def key_of(a, nid):
    """Vocabulary key of a node: program name, or port for network nodes."""
    if a["binary"] == "NET":
        return "net:" + nid.rsplit(":", 1)[1]
    if a["binary"] == "?":
        return "?"
    return os.path.basename(a["binary"])


def build_vocab(graphs):
    keys = set()
    for g in graphs:
        for n, a in g.nodes(data=True):
            keys.add(key_of(a, n))
    return {k: i + 1 for i, k in enumerate(sorted(keys))}      # 0 = unknown


def encode(g, vocab):
    nodes = list(g.nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    V = len(vocab) + 1
    x = torch.zeros(len(nodes), V + 6)
    for n, i in idx.items():
        a = g.nodes[n]
        x[i, vocab.get(key_of(a, n), 0)] = 1.0                 # one-hot program / port
        x[i, V + 0] = 1.0 if a["binary"] == "NET" else 0.0
        x[i, V + 1] = 1.0 if a["uid"] == 0 else 0.0
        x[i, V + 2] = math.log1p(a["n_connect"])
        x[i, V + 3] = math.log1p(a["n_mprotect"])
        x[i, V + 4] = math.log1p(a["n_ptrace"])
        x[i, V + 5] = 1.0 if a["wx"] > 0 else 0.0
    # collapse repeated edges into one weighted edge per (src, dst, relation)
    counts = collections.Counter((idx[u], idx[v], REL[d["rel"]]) for u, v, d in g.edges(data=True))
    src = [k[0] for k in counts]
    dst = [k[1] for k in counts]
    typ = [k[2] for k in counts]
    w = [math.log1p(c) for c in counts.values()]
    edge_index = torch.tensor([src, dst], dtype=torch.long) if src else torch.zeros((2, 0), dtype=torch.long)
    return Data(x=x, edge_index=edge_index,
                edge_type=torch.tensor(typ, dtype=torch.long),
                edge_weight=torch.tensor(w, dtype=torch.float))


def graphs_for(pairs):
    out = []
    for path, name in pairs:
        for g in windows(load(path, name)):
            if g.number_of_nodes() > 0:
                out.append(g)
    return out


if __name__ == "__main__":
    nx_sets = {k: graphs_for(v) for k, v in SETS.items()}
    vocab = build_vocab(nx_sets["train"])          # vocabulary from TRAIN only: no leakage
    data = {k: [encode(g, vocab) for g in gs] for k, gs in nx_sets.items()}
    unk_col = 0
    for k, ds in data.items():
        n = sum(d.num_nodes for d in ds)
        unk = sum(int(d.x[:, unk_col].sum().item()) for d in ds)
        e = sum(d.edge_index.shape[1] for d in ds)
        wx = sum(int(d.x[:, len(vocab) + 6].sum().item()) for d in ds)
        print("%-7s graphs=%-3d nodes=%-5d edges=%-5d unknown-nodes=%-3d (%.1f%%) wx-nodes=%d"
              % (k, len(ds), n, e, unk, 100.0 * unk / max(n, 1), wx))
        for d in ds:                                   # structural sanity checks
            assert d.x.shape[1] == len(vocab) + 7
            assert d.edge_index.shape[1] == d.edge_type.shape[0] == d.edge_weight.shape[0]
            assert d.edge_index.numel() == 0 or int(d.edge_index.max()) < d.num_nodes
    os.makedirs("data", exist_ok=True)
    torch.save({"vocab": vocab, **data}, "data/graphs.pt")
    json.dump(vocab, open("data/vocab.json", "w"), indent=1)
    print("vocab size:", len(vocab), "feature dim:", len(vocab) + 7)
    print("ENCODE OK")
