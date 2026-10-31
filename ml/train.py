"""train.py - trains an R-GCN autoencoder on NORMAL windows only.
Run from the project root: python3 ml/train.py"""
import json, random
import torch, torch.nn as nn
from torch_geometric.nn import RGCNConv
from torch_geometric.loader import DataLoader

torch.manual_seed(0)
random.seed(0)


class RGCNAE(nn.Module):
    def __init__(self, in_dim, hid=32, lat=8, rels=3):
        super().__init__()
        self.c1 = RGCNConv(in_dim, hid, rels)
        self.c2 = RGCNConv(hid, lat, rels)
        self.dec = nn.Sequential(nn.Linear(lat, hid), nn.ReLU(), nn.Linear(hid, in_dim))

    def forward(self, x, edge_index, edge_type):
        h = torch.relu(self.c1(x, edge_index, edge_type))
        z = self.c2(h, edge_index, edge_type)
        return self.dec(z)


def node_errors(model, d):
    out = model(d.x, d.edge_index, d.edge_type)
    return ((out - d.x) ** 2).mean(dim=1)


@torch.no_grad()
def window_scores(model, graphs):
    model.eval()
    res = []
    for d in graphs:
        e = node_errors(model, d)
        res.append((e.max().item(), e.mean().item()))
    return res


def summary(name, scores, thr):
    mx = [s[0] for s in scores]
    flagged = sum(1 for m in mx if m > thr)
    print("%-7s windows=%-3d max-node-error: min=%.4f median=%.4f max=%.4f  flagged=%d (%.1f%%)"
          % (name, len(mx), min(mx), sorted(mx)[len(mx) // 2], max(mx),
             flagged, 100.0 * flagged / len(mx)))
    return flagged


if __name__ == "__main__":
    blob = torch.load("data/graphs.pt", weights_only=False)   # contains PyG Data objects
    train, val, attack = blob["train"], blob["val"], blob["attack"]
    if len(train) < 20 or len(val) < 5:
        raise SystemExit('DATA TOO SMALL: train=%d val=%d windows (need >=20 and >=5). Re-record data.'
                         % (len(train), len(val)))
    in_dim = train[0].x.shape[1]
    print("graphs: train=%d val=%d attack=%d feature-dim=%d" % (len(train), len(val), len(attack), in_dim))

    model = RGCNAE(in_dim)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loader = DataLoader(train, batch_size=16, shuffle=True)

    first = last = None
    for epoch in range(1, 301):
        model.train()
        total, n = 0.0, 0
        for b in loader:
            opt.zero_grad()
            out = model(b.x, b.edge_index, b.edge_type)
            loss = ((out - b.x) ** 2).mean()
            loss.backward()
            opt.step()
            total += loss.item() * b.num_nodes
            n += b.num_nodes
        ep_loss = total / n
        first = ep_loss if first is None else first
        last = ep_loss
        if epoch % 50 == 0 or epoch == 1:
            print("epoch %3d  loss %.5f" % (epoch, ep_loss))

    tr = window_scores(model, train)
    thr = 1.5 * max(s[0] for s in tr)       # from TRAIN only
    print("threshold (1.5 x max train window score): %.4f" % thr)
    summary("train", tr, thr)
    fp = summary("val", window_scores(model, val), thr)
    det = summary("attack", window_scores(model, attack), thr)

    for d in attack:                       # which nodes look strange?
        e = node_errors(model, d).detach()
        top = torch.topk(e, min(3, len(e)))
        print("attack window top node errors:", [round(v, 4) for v in top.values.tolist()])

    torch.save(model.state_dict(), "data/model.pt")
    json.dump({"threshold": thr}, open("data/threshold.json", "w"))
    ok = last < first * 0.5
    print("loss %.5f -> %.5f" % (first, last))
    print("val false positives: %d / %d windows; attack windows flagged: %d / %d"
          % (fp, len(val), det, len(attack)))
    print("TRAIN OK" if ok else "TRAIN FAILED: loss did not halve")
