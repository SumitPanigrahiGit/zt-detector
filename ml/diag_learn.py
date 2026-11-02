import glob, sys, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode, key_of
from train import RGCNAE, window_scores


def rw(f, names, skip=False):
    out = []
    for n in names:
        ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
        out += ws[1:] if skip else ws
    return out


run = rw("data/pyl_1.jsonl", ["zt-py", "zt-pclient"])[:12]
atk = [g for f in sorted(glob.glob("data/pya_beacon_*.jsonl")) for g in rw(f, ["zt-py"], True)]
vocab = build_vocab(run)
print("vocab:", sorted(vocab))
for g in atk[:2]:
    print("attack window node keys:", sorted(set(key_of(a, n) for n, a in g.nodes(data=True))))
tr = [encode(g, vocab) for g in run]
at = [encode(g, vocab) for g in atk]
torch.manual_seed(0)
random.seed(0)
model = RGCNAE(tr[0].x.shape[1])
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loader = DataLoader(tr, batch_size=12, shuffle=True)
for _ in range(300):
    model.train()
    for b in loader:
        opt.zero_grad()
        loss = ((model(b.x, b.edge_index, b.edge_type) - b.x) ** 2).mean()
        loss.backward()
        opt.step()
ts = [s[0] for s in window_scores(model, tr)]
print("train scores:", [round(x, 4) for x in ts])
print("threshold:", round(float(np.percentile(ts, 99)) * 1.5, 4))
print("attack scores:", [round(s[0], 4) for s in window_scores(model, at)])
print("unknown-column nodes per attack window:", [int(d.x[:, 0].sum().item()) for d in at])
