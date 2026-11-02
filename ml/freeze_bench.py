"""freeze_bench.py - time to freeze a container three ways.
Run: sudo .venv/bin/python ml/freeze_bench.py"""
import http.client, os, socket, statistics, subprocess, time


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, check=True).stdout.strip()


class Unix(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.connect("/var/run/docker.sock")


def api(method, path):
    c = Unix()
    c.request(method, path)
    r = c.getresponse()
    r.read()
    c.close()
    return r.status


def cg_path(cid):
    for p in ("/sys/fs/cgroup/system.slice/docker-%s.scope" % cid, "/sys/fs/cgroup/docker/%s" % cid):
        if os.path.isdir(p):
            return p
    raise SystemExit("cgroup path not found")


def state(p):
    for line in open(p + "/cgroup.events"):
        if line.startswith("frozen"):
            return int(line.split()[1])


def wait(p, want):
    end = time.perf_counter() + 2
    while state(p) != want:
        if time.perf_counter() > end:
            raise SystemExit("timeout waiting for frozen=%d" % want)


def m_cli(cid, p, on):
    sh("docker", "pause" if on else "unpause", cid)


def m_api(cid, p, on):
    st = api("POST", "/containers/%s/%s" % (cid, "pause" if on else "unpause"))
    assert st == 204, st


def m_cg(cid, p, on):
    with open(p + "/cgroup.freeze", "w") as f:
        f.write("1" if on else "0")


sh("docker", "rm", "-f", "zt-frz") if "zt-frz" in sh("docker", "ps", "-a", "--format", "{{.Names}}") else None
cid = sh("docker", "run", "-d", "--name", "zt-frz", "alpine", "sleep", "600")
res = {}
try:
    p = cg_path(cid)
    for name, fn in (("docker CLI", m_cli), ("docker API", m_api), ("cgroup.freeze", m_cg)):
        ts = []
        for _ in range(20):
            t0 = time.perf_counter()
            fn(cid, p, True)
            wait(p, 1)
            ts.append((time.perf_counter() - t0) * 1000)
            fn(cid, p, False)
            wait(p, 0)
        res[name] = ts
finally:
    sh("docker", "rm", "-f", "zt-frz")

print("time from request until the kernel reports frozen=1 (ms, 20 runs each)")
for name, ts in res.items():
    ts = sorted(ts)
    print("%-14s median %.2f  p95 %.2f  max %.2f" % (name, statistics.median(ts), ts[18], ts[-1]))
print("FREEZE DONE")
