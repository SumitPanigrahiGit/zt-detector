p = "ml/evaluate_learn.py"
s = open(p).read()
if "thr_steady" in s:
    raise SystemExit("already patched")
old1 = "            thr = float(np.percentile([s[0] for s in window_scores(model, tr)], 99)) * 1.5\n"
new1 = ("            sc = [s[0] for s in window_scores(model, tr)]\n"
        "            st = [bool(d.x[0, -1] > 0.5) for d in tr]\n"
        "            steady = [a for a, k in zip(sc, st) if not k] or sc\n"
        "            start = [a for a, k in zip(sc, st) if k] or sc\n"
        "            thr_steady = max(steady) * 1.5\n"
        "            thr_start = max(start) * 1.5\n")
old2 = "                f = sum(s[0] > thr for s in window_scores(model, enc(data)))\n"
new2 = ("                ed = enc(data)\n"
        "                f = sum(a[0] > (thr_start if bool(d.x[0, -1] > 0.5) else thr_steady)\n"
        "                        for a, d in zip(window_scores(model, ed), ed))\n")
assert s.count(old1) == 1 and s.count(old2) == 1, "anchor not found"
open(p, "w").write(s.replace(old1, new1).replace(old2, new2))
print("patched")
