"""controller.py FILE [--act] [--seconds N] - follows the loader's JSONL output, scores closed windows,
and freezes a flagged container (only with --act). Run from the project root as root."""
import argparse, glob, json, sys, time
from graph_build import Events, windows, WINDOW_NS
from baseline import train_baseline, is_flagged


def now_ns():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def cgroup_dir(cid12):
    for pat in ("/sys/fs/cgroup/system.slice/docker-%s*.scope" % cid12, "/sys/fs/cgroup/docker/%s*" % cid12):
        m = glob.glob(pat)
        if m:
            return m[0]
    return None


def freeze(cid12):
    d = cgroup_dir(cid12)
    if not d:
        return False
    with open(d + "/cgroup.freeze", "w") as f:
        f.write("1")
    return True


def log(msg):
    print("%d %s" % (now_ns(), msg), flush=True)


def tick(entries, base, args):
    for name, c in entries.items():
        if c["done"] or not c["ev"]:
            continue
        if c["image"] != args.image:
            if not c["warned"]:
                log("UNMONITORED %s image=%s" % (name, c["image"]))
                c["warned"] = True
            continue
        ev = c["ev"]
        ev.sort(key=lambda e: e["ts_ns"])
        t0 = ev.start if (ev.start is not None and not ev.pre) else ev[0]["ts_ns"]
        full = (now_ns() - t0) // WINDOW_NS
        limit = t0 + full * WINDOW_NS
        sub = Events(e for e in ev if e["ts_ns"] < limit)
        sub.start, sub.pre, sub.image = ev.start, ev.pre, ev.image
        if not sub:
            continue
        ws = windows(sub)
        for g in ws[c["scored"]:]:
            flagged, s, thr = is_flagged(base, g)
            log("WINDOW %s startup=%d score=%.4f thr=%.4f flagged=%d" % (name, g.graph["startup"], s, thr, flagged))
            if flagged:
                c["done"] = True
                if args.act:
                    t = now_ns()
                    ok = freeze(c["id"])
                    log("FROZEN %s ok=%s ts_ns=%d freeze_ms=%.3f" % (name, ok, now_ns(), (now_ns() - t) / 1e6))
                else:
                    log("WOULD FREEZE %s (dry run)" % name)
                break
        c["scored"] = len(ws)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--act", action="store_true")
    ap.add_argument("--image", default="python:alpine")
    ap.add_argument("--seconds", type=int, default=120)
    args = ap.parse_args()
    base = train_baseline()
    log("READY thresholds steady=%.4f startup=%.4f act=%s" % (base["ts"], base["tt"], args.act))
    entries, buf = {}, ""
    f = open(args.file)
    end = time.time() + args.seconds
    while time.time() < end:
        buf += f.read()
        lines = buf.split("\n")
        buf = lines.pop()
        for line in lines:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            name = e.get("name")
            if e["type"] == "container_start":
                ev = Events()
                ev.start, ev.pre, ev.image = e["ts_ns"], bool(e.get("preexisting", 0)), e.get("image")
                entries[name] = {"ev": ev, "id": e["container"], "image": e.get("image"),
                                 "scored": 0, "done": False, "warned": False}
            elif e["type"] == "container_stop":
                if name in entries:
                    entries[name]["done"] = True
            elif name in entries:
                entries[name]["ev"].append(e)
        tick(entries, base, args)
        time.sleep(0.2)
    log("END")


if __name__ == "__main__":
    main()
