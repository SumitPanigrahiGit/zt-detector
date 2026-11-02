"""evaluate_ps.py - one model per service. Run from the project root."""
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


def fit(train_g, seed):
    vocab = build_vocab(train_g)
    enc = lambda gl: [encode(g, vocab) for g in gl]
    tr = enc(train_g)
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
    thr = float(np.percentile([s[0] for s in window_scores(model, tr)], 99)) * 1.5
    return model, enc, thr


tot, poss = {}, {}


def score(label, model, enc, thr, data):
    f = sum(s[0] > thr for s in window_scores(model, enc(data)))
    tot[label] = tot.get(label, 0) + f
    poss[label] = poss.get(label, 0) + len(data)


for seed in range(5):
    m, enc, thr = fit(n_tr, seed)
    score("nginx model: nginx val", m, enc, thr, n_va)
    for k, v in atk.items():
        score("nginx model: atk " + k, m, enc, thr, v)
    score("nginx model: redis val (wrong service)", m, enc, thr, r_va)
    m, enc, thr = fit(r_tr, seed)
    score("redis model: redis val", m, enc, thr, r_va)
    score("redis model: nginx val (wrong service)", m, enc, thr, n_va)
    print("seed %d done" % seed)

print("\nSUMMARY (counts over 5 seeds)")
for k in tot:
    print("%-42s flagged: %d / %d" % (k, tot[k], poss[k]))
print("EVALPS DONE")
