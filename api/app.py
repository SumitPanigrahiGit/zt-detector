"""app.py - read-only telemetry API plus unfreeze. Run: sudo .venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000"""
import glob, json, os, re, subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

EVENTS = os.environ.get("ZT_EVENTS", "/tmp/zt_live.jsonl")
CTL = os.environ.get("ZT_CTL", "/tmp/zt_ctl.txt")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
app = FastAPI(title="zt-detector telemetry")


def tail_lines(path, max_bytes=1_000_000):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    lines = data.split("\n")
    return lines[1:] if size > max_bytes else lines


def cgroup_dir(cid):
    for pat in ("/sys/fs/cgroup/system.slice/docker-%s*.scope" % cid, "/sys/fs/cgroup/docker/%s*" % cid):
        m = glob.glob(pat)
        if m:
            return m[0]
    return None


def frozen_state(cid):
    d = cgroup_dir(cid)
    if not d:
        return None
    try:
        for line in open(d + "/cgroup.events"):
            if line.startswith("frozen"):
                return int(line.split()[1])
    except OSError:
        return None


@app.get("/health")
def health():
    return {"ok": True, "events_file": os.path.exists(EVENTS), "controller_log": os.path.exists(CTL)}


@app.get("/events")
def events(limit: int = 100):
    limit = max(1, min(limit, 1000))
    out = []
    for line in tail_lines(EVENTS)[-limit:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


@app.get("/containers")
def containers():
    seen = {}
    for line in tail_lines(EVENTS):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "container_start":
            seen[e["name"]] = {"name": e["name"], "id": e["container"], "image": e.get("image"), "stopped": False}
        elif e.get("type") == "container_stop" and e.get("name") in seen:
            seen[e["name"]]["stopped"] = True
    for c in seen.values():
        c["frozen"] = None if c["stopped"] else frozen_state(c["id"])
    return list(seen.values())


@app.get("/alerts")
def alerts(limit: int = 50):
    limit = max(1, min(limit, 500))
    keep = [l for l in tail_lines(CTL) if "flagged=1" in l or "FROZEN" in l or "WOULD FREEZE" in l or "UNMONITORED" in l]
    return keep[-limit:]


@app.post("/unfreeze/{name}")
def unfreeze(name: str):
    if not NAME_RE.match(name):
        raise HTTPException(400, "invalid container name")
    try:
        cid = subprocess.run(["docker", "inspect", "-f", "{{.Id}}", name], capture_output=True, text=True,
                             check=True, timeout=5).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        raise HTTPException(404, "no such running container")
    d = cgroup_dir(cid)
    if not d:
        raise HTTPException(404, "cgroup not found")
    with open(d + "/cgroup.freeze", "w") as f:
        f.write("0")
    return {"name": name, "frozen": frozen_state(cid)}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    with open(os.path.join(os.path.dirname(__file__), "dashboard.html")) as f:
        return f.read()
