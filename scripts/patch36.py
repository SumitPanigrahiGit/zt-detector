def rep(s, old, new, name):
    assert s.count(old) == 1, name + ": anchor not found: " + old[:60]
    return s.replace(old, new)

g = open("ml/graph_build.py").read()
if "AGE_MODE" in g:
    raise SystemExit("already patched")

g = rep(g, "WINDOW_NS = 10 * 10**9   # 10 s snapshots\n",
        'WINDOW_NS = 10 * 10**9   # 10 s snapshots\n'
        'AGE_MODE = os.environ.get("ZT_AGE", "real")   # "real" or "proxy" (old behaviour)\n', "const")

g = rep(g, "def load(path, name=None):\n    events = []\n", r'''class Events(list):
    """List of events plus the container's start info from its container_start record."""
    start = None
    pre = False


def load(path, name=None):
    events = Events()
''', "load")

g = rep(g, '        if e["type"].startswith("container_"):\n            continue\n', r'''        if e["type"].startswith("container_"):
            if e["type"] == "container_start" and e.get("name") == name and events.start is None:
                events.start = e["ts_ns"]
                events.pre = bool(e.get("preexisting", 0))
            continue
''', "skip")

g = rep(g, '    t0 = events[0]["ts_ns"]\n    for e in events:\n        buckets[(e["ts_ns"] - t0) // size].append(e)\n', r'''    start = getattr(events, "start", None)
    pre = getattr(events, "pre", False)
    anchored = AGE_MODE == "real" and start is not None and not pre
    t0 = start if anchored else events[0]["ts_ns"]
    for e in events:
        buckets[max(0, (e["ts_ns"] - t0) // size)].append(e)
''', "buckets")

g = rep(g, "        gr.graph['startup'] = 1 if i == 0 else 0   # first window of the container's recording\n", r'''        if AGE_MODE == "real" and start is not None:
            gr.graph['startup'] = 1 if (anchored and k == 0) else 0
        else:
            gr.graph['startup'] = 1 if i == 0 else 0   # old proxy; also the fallback without a container_start event
''', "flag")

open("ml/graph_build.py", "w").write(g)
print("patched")
