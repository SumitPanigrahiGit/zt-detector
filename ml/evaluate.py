"""evaluate.py - trains on normal2_train, threshold from train only, per-attack results."""
import torch, random, numpy as np
from graph_build import load, windows
from encode import build_vocab, encode
from train import RGCNAE, window_scores
from torch_geometric.loader import DataLoader

NAMES = ["zt-proxy", "zt-backend"]


def gs(path, names):
    out = []
    for n in names:
        out += [g for g in windows(load(path, n)) if g.number_of_nodes() > 0]
    return out


seeds = [0, 1, 2]
train_g = gs("data/normal2_train.jsonl", NAMES)
val_g = gs("data/normal2_val.jsonl", NAMES)
att = {k: gs("data/stealth_%s.jsonl" % k, ["zt-victim"]) for k in ["beacon", "scan", "burst", "wx"]}
vocab = build_vocab(train_g)
tr = [encode(g, vocab) for g in train_g]
va = [encode(g, vocab) for g in val_g]
at = {k: [encode(g, vocab) for g in v] for k, v in att.items()}
print("train=%d val=%d attack windows: %s" % (len(tr), len(va), {k: len(v) for k, v in at.items()}))
empty = [k for k, v in at.items() if len(v) == 0]
if empty:
    raise SystemExit('NO WINDOWS for attacks: %s (re-record them)' % empty)
if len(tr) < 20 or len(va) < 5:
    raise SystemExit("DATA TOO SMALL")

fp_all, hit_all = [], {k: [] for k in at}
for seed in seeds:
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
    fp_all.append(fp / len(va))
    line = ["seed %d thr=%.4f val-FP=%d/%d" % (seed, thr, fp, len(va))]
    for k, v in at.items():
        flagged = sum(s[0] > thr for s in window_scores(model, v))
        hit_all[k].append(flagged / max(len(v), 1))
        line.append("%s %d/%d" % (k, flagged, len(v)))
    print("  ".join(line))

print("\nSUMMARY over %d seeds" % len(seeds))
print("validation false-positive rate: mean %.1f%%" % (100 * np.mean(fp_all)))
for k, v in hit_all.items():
    print("%-7s windows flagged: mean %.0f%%" % (k, 100 * np.mean(v)))
print("EVAL DONE")
