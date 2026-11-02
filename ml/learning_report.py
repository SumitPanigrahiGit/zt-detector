"""learning_report.py FILE NAME L - lists programs and destinations first seen in the learning period."""
import sys
from graph_build import load, windows
from encode import key_of
f, name, L = sys.argv[1], sys.argv[2], int(sys.argv[3])
ws = [g for g in windows(load(f, name)) if g.number_of_nodes() > 0][:L]
seen = {}
for i, g in enumerate(ws):
    for n, a in g.nodes(data=True):
        k = key_of(a, n)
        seen.setdefault(k, i)
print("items observed during learning (first window index):")
for k, i in sorted(seen.items(), key=lambda x: x[1]):
    print("  window %2d  %s" % (i, k))
