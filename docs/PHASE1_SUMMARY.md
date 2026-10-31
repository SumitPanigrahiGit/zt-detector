# Phase 1 Summary: kernel tracing pipeline

Platform: WSL2, Ubuntu 24.04, kernel 6.18. Absolute numbers will differ on bare metal.

## Delivered
- Five tracepoints: execve, connect (IPv4 and IPv6), ptrace, mprotect (PROT_EXEC), process exit
- One ring buffer, tagged-union events with PID, PPID, UID, cgroup ID and payload
- Container attribution by cgroup ID, container ID and name, plus start and stop events
- Fail-open in-kernel host filter, drop counter, JSON Lines export
- Normal-behaviour dataset: nginx proxy and backend (train and validation recordings)
- Attack simulation, rule-based detections, tests, audit and benchmark scripts

## Measured
- Idle loader CPU: 0.2 to 0.4% of one core
- 3000-process exec storm, all events streamed: about 2.6% of one core
- Same storm with the in-kernel container filter: about 0% loader CPU, about 0.6 microseconds per filtered event
- Kernel timestamp to callback latency (light load, WSL2): p50 about 70 to 90 us, p99 about 200 to 300 us. This is not end-to-end detection time.
- Attack demo: one simulated hijack flagged by four signals (ptrace, W+X memory, shell spawn, new destination)
- Rule false positives on validation traffic: 0 alerts for zt-proxy and zt-backend (baseline is near-constant, so this is a weak test)

## Limits
See docs/ARCHITECTURE.md. The baseline is small and uniform, the rules are tuned to one attack, and latency does not include model or containment time.

## Next: Phase 2
Process graphs and a GNN trained on normal behaviour only (started: Days 29 to 31).
