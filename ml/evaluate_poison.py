"""evaluate_poison.py - jitter false positives and poisoning. Run from the project root."""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

NORM = ["zt-py", "zt-pclient"]


def rw(f, names, skip=False):
    out = []
    for n in names:
        ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
        out += ws[1:] if skip else ws
    return out


clean = [rw(f, NORM) for f in sorted(glob.glob("data/pyl_*.jsonl"))]
poison = [rw(f, NORM) for f in sorted(glob.glob("data/pyp_*.jsonl"))]
jit = [g for f in sorted(glob.glob("data/pyj_*.jsonl")) for g in rw(f, NORM)]
reg = [g for f in sorted(glob.glob("data/pyv_*.jsonl")) for g in rw(f, NORM)]
beacon = [g for f in sorted(glob.glob("data/pya_beacon_*.jsonl")) for g in rw(f, ["zt-py"], True)]
print("clean runs", [len(r) for r in clean], "poisoned runs", [len(r) for r in poison],
      "jitter windows", len(jit), "regular val windows", len(reg), "beacon windows", len(beacon))
if len(poison) < 2 or len(jit) < 8 or len(beacon) < 5:
    raise SystemExit("TOO LITTLE DATA (re-record)")

L = 12
TESTS = {"regular val": reg, "jitter val": jit, "beacon": beacon}


def fit_score(train_g, seed):
    vocab = build_vocab(train_g)
    enc = lambda gl: [encode(g, vocab) for g in gl]
    tr = enc(train_g)
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
    ts, tt = max(steady) * 1.5, max(start) * 1.5
    out = {}
    for name, data in TESTS.items():
        ed = enc(data)
        out[name] = sum(a[0] > (tt if bool(d.x[0, -1] > 0.5) else ts)
                        for a, d in zip(window_scores(model, ed), ed))
    return out


res = {}
for setup, runs in (("clean-trained", clean), ("poisoned-trained", poison)):
    for seed in range(3):
        for run in runs:
            r = fit_score(run[:L], seed)
            for k, v in r.items():
                a, b = res.get((setup, k), (0, 0))
                res[(setup, k)] = (a + v, b + len(TESTS[k]))

print("\nSUMMARY (L=12 learning windows; counts over runs x 3 seeds)")
for setup in ("clean-trained", "poisoned-trained"):
    for k in TESTS:
        f, t = res[(setup, k)]
        print("%-17s %-12s flagged: %d / %d" % (setup, k, f, t))
print("EVALPOISON DONE")
