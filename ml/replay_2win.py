"""replay_2win.py - does requiring 2 consecutive flagged windows cut false alarms, and what does it cost?
Run from the project root."""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

NORM = ["zt-py", "zt-pclient"]


def seqs(f, names, skip=False):
    out = []
    for n in names:
        ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
        out.append(ws[1:] if skip else ws)
    return out


learn = [[g for s in seqs(f, NORM) for g in s] for f in sorted(glob.glob("data/pyjl_*.jsonl"))]
normal = [s for f in ("data/pyj_3.jsonl", "data/pyj_4.jsonl") for s in seqs(f, NORM)]
attacks = {k: [s for f in sorted(glob.glob("data/pya_%s_*.jsonl" % k)) for s in seqs(f, ["zt-py"], True)]
           for k in ("beacon", "burst")}
print("learn runs", [len(r) for r in learn], "normal sequences", len(normal),
      "attack recordings", {k: len(v) for k, v in attacks.items()})
if len(learn) < 2 or len(normal) < 4 or min(len(v) for v in attacks.values()) < 5:
    raise SystemExit("TOO LITTLE DATA")


def fit(win, seed):
    vocab = build_vocab(win)
    enc = lambda gl: [encode(g, vocab) for g in gl]
    tr = enc(win)
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
    return model, enc, max(steady) * 1.5, max(start) * 1.5


def flags(model, enc, ts, tt, seq):
    ed = enc(seq)
    return [a[0] > (tt if bool(d.x[0, -1] > 0.5) else ts)
            for a, d in zip(window_scores(model, ed), ed)]


def two(fl):
    return [fl[i] and fl[i - 1] for i in range(1, len(fl))]


nw = k1 = k2 = 0
det = {k: [0, 0, 0] for k in attacks}
for seed in range(3):
    for win in learn:
        model, enc, ts, tt = fit(win[:12], seed)
        for s in normal:
            fl = flags(model, enc, ts, tt, s)
            nw += len(fl)
            k1 += sum(fl)
            k2 += sum(two(fl))
        for k, ss in attacks.items():
            for s in ss:
                fl = flags(model, enc, ts, tt, s)
                det[k][0] += any(fl)
                det[k][1] += any(two(fl))
                det[k][2] += 1

print("\nSUMMARY (rule A thresholds, jittered learning L=12; counts over 2 learning runs x 3 seeds)")
print("normal windows: %d   flagged windows (act on 1): %d   alerts needing 2 in a row: %d" % (nw, k1, k2))
for k, (a, b, n) in det.items():
    print("%-7s recordings detected  act-on-1: %d / %d   2-in-a-row: %d / %d" % (k, a, n, b, n))
print("REPLAY DONE")
