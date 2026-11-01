"""evaluate_ws.py - does the model generalise across services?
Run from the project root: python3 ml/evaluate_ws.py"""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

NG = ["zt-proxy", "zt-backend"]
RG = ["zt-redis", "zt-rclient"]
KINDS = ["beacon", "scan", "burst", "wx"]


def gs(files, names, skip_first=False):
    out = []
    for f in files:
        for n in names:
            ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
            out += ws[1:] if skip_first else ws
    return out


n_tr = gs(sorted(glob.glob("data/n3_train_*.jsonl")), NG)
n_va = gs(sorted(glob.glob("data/n3_val_*.jsonl")), NG)
r_tr = gs(sorted(glob.glob("data/r_train_*.jsonl")), RG)
r_va = gs(sorted(glob.glob("data/r_val_*.jsonl")), RG)
atk = {k: gs(sorted(glob.glob("data/atk_%s_*.jsonl" % k)), ["zt-victim"], True) for k in KINDS}
print("nginx train=%d val=%d | redis train=%d val=%d" % (len(n_tr), len(n_va), len(r_tr), len(r_va)))
if len(r_tr) < 20 or len(r_va) < 5:
    raise SystemExit("TOO FEW REDIS WINDOWS (re-record)")


def train_model(tr, seed):
    torch.manual_seed(seed)
    random.seed(seed)
    model = RGCNAE(tr[0].x.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(tr, batch_size=16, shuffle=True)
    for _ in range(300):
        model.train()
        for b in loader:
            opt.zero_grad()
            loss = ((model(b.x, b.edge_index, b.edge_type) - b.x) ** 2).mean()
            loss.backward()
            opt.step()
    return model


tot, poss = {}, {}
for seed in range(5):
    for setup, train_g in (("nginx-only", n_tr), ("both", n_tr + r_tr)):
        vocab = build_vocab(train_g)
        enc = lambda gl: [encode(g, vocab) for g in gl]
        tr = enc(train_g)
        model = train_model(tr, seed)
        thr = float(np.percentile([s[0] for s in window_scores(model, tr)], 99)) * 1.5
        tests = [("nginx val", enc(n_va)), ("redis val", enc(r_va))]
        tests += [("atk " + k, enc(v)) for k, v in atk.items()]
        for name, data in tests:
            f = sum(s[0] > thr for s in window_scores(model, data))
            tot[(setup, name)] = tot.get((setup, name), 0) + f
            poss[(setup, name)] = poss.get((setup, name), 0) + len(data)
        print("seed %d %s done thr=%.4f" % (seed, setup, thr))

print("\nSUMMARY (counts over 5 seeds)")
for setup in ("nginx-only", "both"):
    for name in ["nginx val", "redis val"] + ["atk " + k for k in KINDS]:
        print("%-10s %-12s flagged: %d / %d" % (setup, name, tot[(setup, name)], poss[(setup, name)]))
print("EVALWS DONE")
