import glob, sys
sys.path.insert(0, "ml")
exec(open("ml/replay_2win.py").read().split("nw = k1 = k2 = 0")[0])
win = learn[0][:12]
print("learn window containers:", [g.graph.get("image") for g in win][:3], "n =", len(win))
model, enc, ts, tt = fit(win, 0)
print("thresholds steady %.4f startup %.4f" % (ts, tt))
merged = [g for s in normal for g in s]
fl = flags(model, enc, ts, tt, merged)
print("merged fresh windows:", len(fl), "flagged:", sum(fl))
for i, s in enumerate(normal):
    f = flags(model, enc, ts, tt, s)
    print("sequence", i, "windows", len(f), "flagged", sum(f))
