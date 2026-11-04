"""baseline.py - trains the python:alpine baseline and scores single windows."""
import glob, random
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores


def learning_windows(pattern="data/pyjl_*.jsonl", L=12):
    runs = []
    for f in sorted(glob.glob(pattern)):
        ws = [g for n in ["zt-py", "zt-pclient"] for g in windows(load(f, n)) if g.number_of_nodes() > 0]
        runs.append(ws[:L])
    return runs


def train_baseline(seed=0):
    run = learning_windows()[0]
    vocab = build_vocab(run)
    tr = [encode(g, vocab) for g in run]
    torch.manual_seed(seed)
    random.seed(seed)
    model = RGCNAE(tr[0].x.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(tr, batch_size=min(16, len(tr)), shuffle=True)
    for _ in range(300):
        model.train()
        for b in loader:
            opt.zero_grad()
            loss = ((model(b.x, b.edge_index, b.edge_type) - b.x) ** 2).mean()
            loss.backward()
            opt.step()
    sc = [s[0] for s in window_scores(model, tr)]
    st = [bool(d.x[0, -1] > 0.5) for d in tr]
    steady = [a for a, k in zip(sc, st) if not k] or sc
    start = [a for a, k in zip(sc, st) if k] or sc
    return {"model": model, "vocab": vocab, "ts": max(steady) * 1.5, "tt": max(start) * 1.5}


def is_flagged(b, g):
    d = encode(g, b["vocab"])
    s = window_scores(b["model"], [d])[0][0]
    thr = b["tt"] if bool(d.x[0, -1] > 0.5) else b["ts"]
    return s > thr, s, thr
