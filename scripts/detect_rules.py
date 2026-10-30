# detect_rules.py BASELINE.jsonl TARGET.jsonl CONTAINER_NAME
# Flags behaviour in TARGET that never appears in the normal baseline.
import json, sys, os

baseline, target, name = sys.argv[1], sys.argv[2], sys.argv[3]

known_exec, known_ports = set(), set()
for line in open(baseline):
    e = json.loads(line)
    if e["type"] == "exec":
        known_exec.add(e["filename"])
    elif e["type"] == "connect":
        known_ports.add(e["port"])

SHELLS = {"sh", "ash", "bash", "dash", "busybox"}
alerts = 0
for line in open(target):
    e = json.loads(line)
    if e.get("name") != name:
        continue
    t = e["type"]
    if t == "exec":
        base = os.path.basename(e["filename"])
        if base in SHELLS:
            print("ALERT shell-spawn   ", e["filename"], "pid", e["pid"]); alerts += 1
        elif e["filename"] not in known_exec:
            print("ALERT new-binary    ", e["filename"], "pid", e["pid"]); alerts += 1
    elif t == "ptrace":
        print("ALERT ptrace        ", e["request_name"], "-> pid", e["target_pid"]); alerts += 1
    elif t == "mprotect" and (e["prot"] & 6) == 6:
        print("ALERT wx-memory     ", "addr", hex(e["addr"]), "prot", e["prot"]); alerts += 1
    elif t == "connect" and e["port"] not in known_ports:
        print("ALERT new-destination", e["ip"] + ":" + str(e["port"])); alerts += 1
print("total alerts:", alerts)
