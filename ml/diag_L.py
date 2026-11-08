import sys
sys.path.insert(0, "ml")
exec(open("ml/replay_2win.py").read().split("nw = k1 = k2 = 0")[0])
for L in (12, 24, 36):
    nflag = ntot = 0
    for seed in range(3):
        for win in learn:
            model, enc, ts, tt = fit(win[:L], seed)
            for s in normal:
                fl = flags(model, enc, ts, tt, s)
                nflag += sum(fl)
                ntot += len(fl)
    print("L=%d normal windows %d flagged %d" % (L, ntot, nflag))
