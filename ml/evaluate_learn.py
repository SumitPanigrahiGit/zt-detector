"""evaluate_learn.py - how long must a new image be observed before its baseline is usable?
Train on the first L windows of ONE learning run; test on separate validation runs and attacks.
Run from the project root."""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

NORM = ["zt-py", "zt-pclient"]


def run_windows(f, names, skip_first=False):
    out = []
    for n in names:
        ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
        out += ws[1:] if skip_first else ws
    return out


learn_runs = [run_windows(f, NORM) for f in sorted(glob.glob("data/pyl_*.jsonl"))]
val_g = [g for f in sorted(glob.glob("data/pyv_*.jsonl")) for g in run_windows(f, NORM)]
atk_g = {k: [g for f in sorted(glob.glob("data/pya_%s_*.jsonl" % k)) for g in run_windows(f, ["zt-py"], True)]
         for k in ("beacon", "burst")}
print("learn runs:", [len(r) for r in learn_runs], "val windows:", len(val_g),
      "attack windows:", {k: len(v) for k, v in atk_g.items()})
if len(learn_runs) < 3 or len(val_g) < 8 or min(len(v) for v in atk_g.values()) < 5:
    raise SystemExit("TOO LITTLE DATA (re-record)")

LS = [6, 12, 18]
res = {}
for L in LS:
    for ri, run in enumerate(learn_runs):
        if len(run) < L:
            continue
        train_g = run[:L]
        vocab = build_vocab(train_g)
        enc = lambda gl: [encode(g, vocab) for g in gl]
        tr = enc(train_g)
        for seed in range(3):
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
            thr = float(np.percentile([s[0] for s in window_scores(model, tr)], 99)) * 1.5
            for name, data in [("val (false positives)", val_g)] + [("atk " + k, v) for k, v in atk_g.items()]:
                f = sum(s[0] > thr for s in window_scores(model, enc(data)))
                key = (L, name)
                a, b = res.get(key, (0, 0))
                res[key] = (a + f, b + len(data))

print("\nSUMMARY (counts over learning runs x 3 seeds; L = learning windows of 10 s)")
for L in LS:
    for name in ["val (false positives)", "atk beacon", "atk burst"]:
        if (L, name) in res:
            f, t = res[(L, name)]
            print("L=%-3d %-22s flagged: %d / %d" % (L, name, f, t))
print("EVALLEARN DONE")
