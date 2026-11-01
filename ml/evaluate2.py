"""evaluate2.py - 5 seeds; threshold from train only; attack startup window dropped.
Run from the project root: python3 ml/evaluate2.py"""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

NAMES = ["zt-proxy", "zt-backend"]
KINDS = ["beacon", "scan", "burst", "wx"]


def gs(files, names, skip_first=False):
    out = []
    for f in files:
        for n in names:
            ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
            out += ws[1:] if skip_first else ws
    return out


train_g = gs(sorted(glob.glob("data/n3_train_*.jsonl")), NAMES)
val_g = gs(sorted(glob.glob("data/n3_val_*.jsonl")), NAMES)
att_g = {k: gs(sorted(glob.glob("data/atk_%s_*.jsonl" % k)), ["zt-victim"], skip_first=True)
         for k in KINDS}
vocab = build_vocab(train_g)
tr = [encode(g, vocab) for g in train_g]
va = [encode(g, vocab) for g in val_g]
at = {k: [encode(g, vocab) for g in v] for k, v in att_g.items()}
print("train=%d val=%d attack windows: %s" % (len(tr), len(va), {k: len(v) for k, v in at.items()}))
empty = [k for k, v in at.items() if len(v) < 3]
if empty:
    raise SystemExit("TOO FEW ATTACK WINDOWS for %s (re-record)" % empty)
if len(tr) < 40 or len(va) < 15:
    raise SystemExit("DATA TOO SMALL")

SEEDS = [0, 1, 2, 3, 4]
fp_total, fp_possible = 0, 0
hits = {k: 0 for k in at}
poss = {k: 0 for k in at}
for seed in SEEDS:
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
    train_s = [s[0] for s in window_scores(model, tr)]
    thr = float(np.percentile(train_s, 99)) * 1.5          # train data only
    fp = sum(s[0] > thr for s in window_scores(model, va))
    fp_total += fp
    fp_possible += len(va)
    parts = ["seed %d thr=%.4f val-FP=%d/%d" % (seed, thr, fp, len(va))]
    for k, v in at.items():
        f = sum(s[0] > thr for s in window_scores(model, v))
        hits[k] += f
        poss[k] += len(v)
        parts.append("%s %d/%d" % (k, f, len(v)))
    print("  ".join(parts))

print("\nSUMMARY (counts over %d seeds)" % len(SEEDS))
print("validation windows flagged: %d / %d" % (fp_total, fp_possible))
for k in at:
    print("%-7s attack windows flagged: %d / %d" % (k, hits[k], poss[k]))
print("EVAL2 DONE")
