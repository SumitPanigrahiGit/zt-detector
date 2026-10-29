import json, sys, collections

for path in sys.argv[1:]:
    types = collections.Counter()
    names = collections.Counter()
    execs = collections.Counter()
    dests = collections.Counter()
    n = 0
    for n, line in enumerate(open(path), 1):
        e = json.loads(line)
        types[e["type"]] += 1
        names[e["name"]] += 1
        if e["type"] == "exec":
            execs[e["filename"]] += 1
        if e["type"] == "connect":
            dests[e["ip"] + ":" + str(e["port"])] += 1
    print("==", path, "-", n, "events")
    print("types:     ", dict(types))
    print("containers:", dict(names))
    print("top execs: ", execs.most_common(5))
    print("top dests: ", dests.most_common(4))

