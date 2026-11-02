"""evaluate_thr.py - 1.5x-max rule vs variation-aware rule on jittered python data.
Run from the project root."""
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


learn = [rw(f, NORM) for f in sorted(glob.glob("data/pyjl_*.jsonl"))]
fresh = [g for f in ("data/pyj_3.jsonl", "data/pyj_4.jsonl") for g in rw(f, NORM)]
beacon = [g for f in sorted(glob.glob("data/pya_beacon_*.jsonl")) for g in rw(f, ["zt-py"], True)]
print("jitter learn runs", [len(r) for r in learn], "fresh jitter windows", len(fresh), "beacon windows", len(beacon))
if len(learn) < 2 or len(fresh) < 8 or len(beacon) < 5:
    raise SystemExit("TOO LITTLE DATA (re-record)")
L = 12
TESTS = {"fresh jitter val": fresh, "beacon": beacon}


def train_model(tr, seed):
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
    return model


def steady_scores(model, ds):
    return [s[0] for s, d in zip(window_scores(model, ds), ds) if not bool(d.x[0, -1] > 0.5)]


def run(win, seed):
    vocab = build_vocab(win)
    enc = lambda gl: [encode(g, vocab) for g in gl]
    tr = enc(win)
    # rule A: 1.5 x max of steady training scores (the old rule)
    m = train_model(tr, seed)
    ma = max(steady_scores(m, tr) or [0.0])
    # rule B: hold out every 3rd steady window, threshold = mean + 3 sd of held-out scores
    hold = [d for i, d in enumerate(tr) if i % 3 == 2 and not bool(d.x[0, -1] > 0.5)]
    fit = [d for d in tr if all(d is not h for h in hold)]
    m2 = train_model(fit, seed)
    hs = steady_scores(m2, hold)
    thr_b = float(np.mean(hs) + 3 * np.std(hs)) if len(hs) >= 3 else ma * 1.5
    out = {}
    for name, data in TESTS.items():
        ed = enc(data)
        sa = [a[0] for a in window_scores(m, ed)]
        sb = [a[0] for a in window_scores(m2, ed)]
        out[name] = (sum(x > ma * 1.5 for x in sa), sum(x > thr_b for x in sb), len(ed))
    return out


tot = {}
for seed in range(3):
    for win in learn:
        r = run(win[:L], seed)
        for k, (a, b, n) in r.items():
            x = tot.get(k, [0, 0, 0])
            tot[k] = [x[0] + a, x[1] + b, x[2] + n]
print("\nSUMMARY (L=12, jittered learning, counts over runs x 3 seeds)")
for k, (a, b, n) in tot.items():
    print("%-17s rule A (1.5 x max): flagged %d / %d   rule B (held-out mean+3sd): flagged %d / %d" % (k, a, n, b, n))
print("EVALTHR DONE")
