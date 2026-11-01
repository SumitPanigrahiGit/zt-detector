"""evaluate_pre.py - model trained on n3_train; tests on already-running containers.
Run from the project root with ZT_AGE=proxy or ZT_AGE=real."""
import glob, os, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores


def gs(files, names):
    out = []
    for f in files:
        for n in names:
            out += [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
    return out


NAMES = ["zt-proxy", "zt-backend"]
train_g = gs(sorted(glob.glob("data/n3_train_*.jsonl")), NAMES)
val_g = gs(sorted(glob.glob("data/n3_val_*.jsonl")), NAMES)
pn_g = gs(sorted(glob.glob("data/pre_norm_*.jsonl")), NAMES)
pb_g = gs(sorted(glob.glob("data/pre_burst_*.jsonl")), ["zt-victim"])
vocab = build_vocab(train_g)
enc = lambda gl: [encode(g, vocab) for g in gl]
tr, va, pn, pb = enc(train_g), enc(val_g), enc(pn_g), enc(pb_g)
print("mode=%s train=%d val=%d pre_norm=%d pre_burst=%d"
      % (os.environ.get("ZT_AGE", "real"), len(tr), len(va), len(pn), len(pb)))
if min(len(pn), len(pb)) < 5:
    raise SystemExit("TOO FEW PRE WINDOWS (record them first)")

tot = {"val": 0, "pre_norm": 0, "pre_burst": 0}
poss = {"val": 0, "pre_norm": 0, "pre_burst": 0}
for seed in range(5):
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
    line = ["seed %d" % seed]
    for k, d in (("val", va), ("pre_norm", pn), ("pre_burst", pb)):
        f = sum(s[0] > thr for s in window_scores(model, d))
        tot[k] += f
        poss[k] += len(d)
        line.append("%s %d/%d" % (k, f, len(d)))
    print("  ".join(line))
print("\nSUMMARY (counts over 5 seeds)")
print("validation windows flagged (false positives): %d / %d" % (tot["val"], poss["val"]))
print("already-running NORMAL windows flagged (false positives): %d / %d" % (tot["pre_norm"], poss["pre_norm"]))
print("already-running BURST windows flagged (detections): %d / %d" % (tot["pre_burst"], poss["pre_burst"]))
print("EVALPRE DONE")
