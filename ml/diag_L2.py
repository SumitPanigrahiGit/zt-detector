import sys
sys.path.insert(0, "ml")
exec(open("ml/replay_2win.py").read().split("nw = k1 = k2 = 0")[0])
for L in (12, 24):
    det = {k: [0, 0] for k in attacks}
    for seed in range(3):
        for win in learn:
            model, enc, ts, tt = fit(win[:L], seed)
            for k, ss in attacks.items():
                for s in ss:
                    det[k][0] += any(flags(model, enc, ts, tt, s))
                    det[k][1] += 1
    print("L=%d" % L, {k: "%d/%d" % tuple(v) for k, v in det.items()})
