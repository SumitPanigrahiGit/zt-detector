# Phase 1 Summary: kernel tracing pipeline

Platform: WSL2, Ubuntu 24.04, kernel 6.18. Absolute numbers will differ on bare metal.

## Delivered
- Five tracepoints: execve, connect (IPv4 and IPv6), ptrace, mprotect (PROT_EXEC), process exit
- One ring buffer, tagged-union events with PID, PPID, UID, cgroup ID and payload
- Container attribution by cgroup ID, container ID and name, plus start and stop events
- Fail-open in-kernel host filter, drop counter, JSON Lines export
- Normal-behaviour dataset: nginx proxy and backend (train and validation recordings)
- Attack simulation and rule-based detections, tests, audit and benchmark scripts

## Measured
- Idle loader CPU: 0.2 to 0.4% of one core
- 3000-process exec storm, all events streamed: about 2.6% of one core
- Same storm with the in-kernel container filter: about 0% loader CPU, about 0.6 microseconds per filtered event
- Kernel to user-space latency under nginx load: <p50 and p99 from Step 2>
- Dropped events in the nginx run: <number from Step 2>
- Attack demo alerts: <list from Step 2>
- Rule false positives on validation traffic: <numbers from Step 2>

## Limits
See docs/ARCHITECTURE.md. The baseline is small, the rules are tuned to one attack, and latency does not yet include model or containment time.

## Next: Phase 2
Process graph construction and a GNN trained on normal behaviour only.
