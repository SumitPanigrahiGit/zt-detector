# Runtime Container Anomaly Detection with eBPF and Graph Neural Networks

Status: a student project built and measured on one machine (WSL2, Ubuntu 24.04, kernel 6.18). Every measured figure below comes from `docs/results-index.md`.

## 1. Problem

Containers share the host kernel, so a compromised process inside one can attempt process injection, beaconing to unusual destinations, or abnormal process spawning. Signature-based tools miss behaviour they have no rule for. This project asks a narrower question: can a model trained only on a container's normal syscall behaviour flag deviations, and can the host contain the container quickly and reversibly?

The project does not claim to detect real exploits. All attacks are scripted simulations of the syscalls such an attack would make.

## 2. Design

1. **Tracing.** eBPF tracepoints on execve, connect (IPv4 and IPv6), ptrace, mprotect (only calls requesting execute permission) and process exit.
2. **Transport.** One ring buffer with a tagged-union event, so event order is kept across syscall types. A per-CPU counter records events lost when the buffer is full.
3. **Attribution.** The kernel knows only the cgroup ID. User space maps it to a container ID, name and image by scanning the Docker cgroup directories and reading Docker's metadata.
4. **Graphs.** Events are grouped into fixed windows per container. Nodes are processes and network destinations; edges are spawned, connected and ptraced relations.
5. **Model.** A two-layer relational graph convolutional autoencoder, trained only on normal windows. A window is flagged when its largest node reconstruction error exceeds a threshold.
6. **Containment.** A controller scores each completed window and, only when run with an explicit flag, freezes the container through its cgroup. Freezing is reversible.

## 3. Implementation notes

- **Fail-open kernel filter.** With the container-only flag, the kernel drops events only from cgroups the loader has confirmed to be host cgroups. Unknown cgroups still reach user space, so a new container's first events are not hidden. A fail-closed version hid them during development.
- **Per-regime thresholds.** Container startup windows score much higher than steady windows. One shared threshold was set by startup windows and made later attacks invisible, so startup and steady windows each get their own threshold (1.5 times the largest training score of that kind).
- **Container age from real start events.** The startup flag comes from the container's start event. A version based on position in the recording produced false positives on containers that were already running.
- **Per-image baselines.** A model trained on two services lost detection on one of them, so each image gets its own model. An image with no baseline is reported as unmonitored rather than as an attack.
- **Dry-run default.** The controller logs what it would freeze and acts only with an explicit flag.
- **Privilege.** The packaged loader runs privileged with host PID access. The API container is read-only and bound to localhost, with no authentication.

Measured results, with their caveats, are in section 4 and in `docs/results-index.md`.

## 4. Evaluation

Each entry shows its source file, status and caveat, followed by lines copied from that file. Counts are window or run counts, not rates. Seeds are not independent samples. Entries marked 'hypothesis failed' are results that contradicted what was expected before testing.

### ## 4.1  Idle and heavy-load loader CPU, per-event cost (last runs)
- source: `docs/bench-results.txt`
- status: **measured**
- caveat: WSL2, noisy; counters accumulate across runs; bench.sh without -c

```
Loader CPU idle:                0.000% of one core
Loader CPU under heavy load:    1.606% of one core
eBPF programs: 24383 events, average 6444.328 ns per event
Loader CPU idle:                0.100% of one core
Loader CPU under heavy load:    1.213% of one core
eBPF programs: 36676 events, average 4418.065 ns per event
Loader CPU idle:                0.000% of one core
Loader CPU under heavy load:    1.449% of one core
eBPF programs: 48969 events, average 3289.699 ns per event
Loader CPU idle:                0.200% of one core
Loader CPU under heavy load:    2.567% of one core
eBPF programs: 15185 events, average 20428.271 ns per event
Loader CPU idle:                0.299% of one core
Loader CPU under heavy load:    2.854% of one core
```

### ## 4.2  Detection with rate and age features, 5 seeds
- source: `docs/results-day35-fresh.txt`
- status: **measured**
- caveat: seeds not independent; beacon/scan/wx include unseen tokens

```
validation windows flagged: 0 / 160
beacon  attack windows flagged: 70 / 70
scan    attack windows flagged: 35 / 35
burst   attack windows flagged: 76 / 80
wx      attack windows flagged: 35 / 35
```

### ## 4.2  Before the age feature (burst missed)
- source: `docs/results-day34-before-age.txt`
- status: **measured**
- caveat: same data, earlier feature set

```
validation windows flagged: 0 / 160
beacon  attack windows flagged: 50 / 50
scan    attack windows flagged: 25 / 25
burst   attack windows flagged: 20 / 50
wx      attack windows flagged: 25 / 25
```

### ## 4.3  Real vs proxy container age on running containers
- source: `docs/results-day36-pre-real.txt`
- status: **measured**
- caveat: short recordings; 5 seeds not independent

```
validation windows flagged (false positives): 0 / 160
already-running NORMAL windows flagged (false positives): 0 / 90
already-running BURST windows flagged (detections): 40 / 50
```

### ## 4.3  Proxy age, same test
- source: `docs/results-day36-pre-proxy.txt`
- status: **measured**
- caveat: compare with the real-age row

```
validation windows flagged (false positives): 0 / 160
already-running NORMAL windows flagged (false positives): 4 / 90
already-running BURST windows flagged (detections): 35 / 50
```

### ## 4.4  Nginx-only vs nginx+redis model
- source: `docs/results-day37.txt`
- status: **measured**
- caveat: attacks only on the nginx image

```
nginx-only nginx val    flagged: 0 / 160
nginx-only redis val    flagged: 140 / 140
nginx-only atk beacon   flagged: 65 / 65
nginx-only atk scan     flagged: 35 / 35
nginx-only atk burst    flagged: 75 / 80
nginx-only atk wx       flagged: 35 / 35
both       nginx val    flagged: 0 / 160
both       redis val    flagged: 1 / 140
both       atk beacon   flagged: 65 / 65
both       atk scan     flagged: 35 / 35
both       atk burst    flagged: 59 / 80
both       atk wx       flagged: 35 / 35
```

### ## 4.4  Per-service baselines
- source: `docs/results-day38.txt`
- status: **measured**
- caveat: service chosen from container names

```
nginx model: nginx val                     flagged: 0 / 160
nginx model: atk beacon                    flagged: 65 / 65
nginx model: atk scan                      flagged: 35 / 35
nginx model: atk burst                     flagged: 75 / 80
nginx model: atk wx                        flagged: 35 / 35
nginx model: redis val (wrong service)     flagged: 140 / 140
redis model: redis val                     flagged: 0 / 140
redis model: nginx val (wrong service)     flagged: 158 / 160
```

### ## 4.4  Poisoning and jitter (L=12)
- source: `docs/results-day41.txt`
- status: **measured**
- caveat: 2 poisoned recordings; one workload

```
clean-trained     regular val  flagged: 0 / 198
clean-trained     jitter val   flagged: 102 / 198
clean-trained     beacon       flagged: 108 / 108
poisoned-trained  regular val  flagged: 0 / 132
poisoned-trained  jitter val   flagged: 0 / 132
poisoned-trained  beacon       flagged: 0 / 72
```

### ## 5  Rule B vs rule A threshold
- source: `docs/results-day42.txt`
- status: **hypothesis failed**
- caveat: identical counts; 4 held-out windows per run

```
fresh jitter val  rule A (1.5 x max): flagged 24 / 132   rule B (held-out mean+3sd): flagged 24 / 132
beacon            rule A (1.5 x max): flagged 72 / 72   rule B (held-out mean+3sd): flagged 72 / 72
```

### ## 4.5  Freeze time by method
- source: `docs/results-day43-freeze.txt`
- status: **measured**
- caveat: 20 runs each; request until kernel reports frozen=1; action only

```
docker CLI     median 55.45  p95 76.88  max 78.67
docker API     median 25.70  p95 33.35  max 35.63
cgroup.freeze  median 0.19  p95 0.33  max 0.35
```

### ## 4.5  Two-window rule at 10 s
- source: `docs/results-day43-replay.txt`
- status: **measured**
- caveat: cost 9 burst detections, removed no false alarms

```
normal windows: 132   flagged windows (act on 1): 0   alerts needing 2 in a row: 0
beacon  recordings detected  act-on-1: 36 / 36   2-in-a-row: 36 / 36
burst   recordings detected  act-on-1: 36 / 36   2-in-a-row: 27 / 36
```

### ## 4.5  Live latency, 10 s windows
- source: `docs/results-day45.txt`
- status: **measured**
- caveat: 8 runs; one scripted attack; latency set by window phase

```
1 31 1 yes 8.04 0
2 33 3 yes 6.24 0
3 35 5 yes 4.12 0
4 37 7 yes 2.18 0
5 39 9 yes 10.28 0
6 41 1 yes 8.28 0
7 43 3 yes 6.22 0
8 45 5 yes 4.19 0
```

### ## 5  5 s windows offline
- source: `docs/results-day46-fp.txt`
- status: **measured**
- caveat: 4 flags are 2 distinct windows

```
normal windows: 252   flagged windows (act on 1): 4   alerts needing 2 in a row: 0
beacon  recordings detected  act-on-1: 36 / 36   2-in-a-row: 36 / 36
burst   recordings detected  act-on-1: 33 / 36   2-in-a-row: 30 / 36
```

### ## 5  5 s windows live, L=12
- source: `docs/results-day47-live5.txt`
- status: **hypothesis failed**
- caveat: normal client flagged in 4 of 6 runs

```
1 31 1 yes 2.62 0
2 33 3 yes 1.00 1
3 35 5 yes 3.93 0
4 37 7 yes 1.96 1
5 39 9 yes 4.79 1
6 41 1 yes 2.94 1
```

### ## 5  5 s windows live, L=24
- source: `docs/results-day48-L24.txt`
- status: **hypothesis failed**
- caveat: 1 of 6 runs flagged the normal client

```
1 31 1 yes 2.65 0
2 33 3 yes 1.03 0
3 35 5 yes 4.09 0
4 37 7 yes 1.84 1
5 39 9 yes 5.00 0
6 41 1 yes 3.00 0
```

### ## 5  5 s, L=24, two in a row
- source: `docs/results-day49-consec2.txt`
- status: **measured**
- caveat: sudo expired mid-run; run valid but suspect

```
1 31 1 yes 8.19 0
2 33 3 yes 6.50 0
3 35 5 yes 9.50 0
4 37 7 yes 7.51 0
5 39 9 yes 5.48 0
6 41 1 yes 8.48 0
```

### ## 4.5  Live latency, API test
- source: `docs/results-day51.txt`
- status: **measured**
- caveat: tiny log; one throwaway container

```
GET /health -> 200 0.026707
GET /events -> 200 0.003314
GET /containers -> 200 0.003329
GET /alerts -> 200 0.002639
before: frozen 1
POST unfreeze -> {"name":"zt-api-t","frozen":0}
after:  frozen 0
```

## 5. Failed hypotheses

- A held-out variation-aware threshold gave counts identical to the simple rule (index, section 5).
- Five-second windows halved latency but flagged a normal client in live runs; longer learning reduced this but did not remove it.
- Requiring two flagged windows in a row removed false freezes at five seconds but raised median latency above that of ten-second windows.
- Requiring two windows at ten seconds removed no false alarms and cost burst detections.

## 6. Limitations

- One machine (WSL2), a few simple workloads, and scripted attacks that only make the relevant syscalls.
- Three of four attacks contain tokens (ports, binaries) never seen in training, which the vocabulary marks as unknown; only the rate-based attack tests behaviour with familiar tokens.
- A baseline learned while a container is already compromised absorbs the attack. The learning report supports human review but does not prevent this.
- Seeds, runs and windows are not independent samples, so counts are not rates.
- The loader runs privileged; the API has no authentication.
- Freeze time measures only the cgroup write, not detection; end-to-end latency is dominated by the window length.

## 7. Future work

Real exploit samples, more and noisier workloads, a temporal model, authentication, and a baseline-integrity check for the learning period.
