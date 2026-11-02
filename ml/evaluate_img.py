"""evaluate_img.py - one model per image; unknown images are 'unmonitored', not alarms.
Run from the project root."""
import glob, random
import numpy as np
import torch
from torch_geometric.loader import DataLoader
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores

# legacy recordings were made before the loader wrote "image"
LEGACY = {"zt-proxy": "nginx:alpine", "zt-backend": "nginx:alpine", "zt-victim": "nginx:alpine",
          "zt-redis": "redis:alpine", "zt-rclient": "redis:alpine"}
NG = ["zt-proxy", "zt-backend"]
RG = ["zt-redis", "zt-rclient"]
KINDS = ["beacon", "scan", "burst", "wx"]


def gs(files, names, skip_first=False):
    out = []
    for f in files:
        for n in names:
            ws = [g for g in windows(load(f, n)) if g.number_of_nodes() > 0]
            ws = ws[1:] if skip_first else ws
            for g in ws:
                if not g.graph.get("image"):
                    g.graph["image"] = LEGACY.get(n, "?")
            out += ws
    return out


train_g = gs(sorted(glob.glob("data/n3_train_*.jsonl")), NG) + gs(sorted(glob.glob("data/r_train_*.jsonl")), RG)
tests = {
    "nginx val": gs(sorted(glob.glob("data/n3_val_*.jsonl")), NG),
    "redis val": gs(sorted(glob.glob("data/r_val_*.jsonl")), RG),
    "python (no baseline)": gs(sorted(glob.glob("data/py_*.jsonl")), ["zt-py", "zt-pclient"]),
}
for k in KINDS:
    tests["atk " + k] = gs(sorted(glob.glob("data/atk_%s_*.jsonl" % k)), ["zt-victim"], True)
by_img = {}
for g in train_g:
    by_img.setdefault(g.graph["image"], []).append(g)
print("train images:", {k: len(v) for k, v in by_img.items()})
print("test windows:", {k: len(v) for k, v in tests.items()})
if len(tests["python (no baseline)"]) < 5:
    raise SystemExit("TOO FEW PYTHON WINDOWS (record them first)")


def fit(gl, seed):
    vocab = build_vocab(gl)
    enc = lambda x: [encode(g, vocab) for g in x]
    tr = enc(gl)
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


stats = {k: [0, 0, 0] for k in tests}      # flagged, unmonitored, total
for seed in range(5):
    models = {img: fit(gl, seed) for img, gl in by_img.items()}
    for name, wins in tests.items():
        for g in wins:
            stats[name][2] += 1
            m = models.get(g.graph["image"])
            if m is None:
                stats[name][1] += 1
                continue
            model, enc, thr = m
            if window_scores(model, enc([g]))[0][0] > thr:
                stats[name][0] += 1
    print("seed %d done" % seed)

print("\nSUMMARY (counts over 5 seeds)")
for name, (f, u, t) in stats.items():
    print("%-22s flagged: %d  unmonitored: %d  total: %d" % (name, f, u, t))
print("EVALIMG DONE")
