import sys
sys.path.insert(0, "ml")
exec(open("ml/replay_2win.py").read().split("nw = k1 = k2 = 0")[0])
for seed in range(3):
    for ri, win in enumerate(learn):
        model, enc, ts, tt = fit(win[:12], seed)
        for si, s in enumerate(normal):
            ed = enc(s)
            for wi, (a, d) in enumerate(zip(window_scores(model, ed), ed)):
                if a[0] > (tt if bool(d.x[0, -1] > 0.5) else ts):
                    print("seed", seed, "learn", ri, "seq", si, "window", wi,
                          "startup", bool(d.x[0, -1] > 0.5), "score %.4f" % a[0])
