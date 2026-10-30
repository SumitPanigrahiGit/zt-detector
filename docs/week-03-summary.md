# Week 3 Summary: Measurement, completeness and dataset

## Built
- Per-container event counters and -q (quiet) flag
- IPv6 connect tracing
- Dropped-event counter (per-CPU BPF array)
- JSON Lines output (-j) for the ML phase
- Normal-behaviour dataset: nginx proxy + backend (train and validation recordings)
- verify_all.sh: one-command re-test of every feature
- record.sh: one-command dataset recording

## Measured overhead (scripts/bench.sh, 3 runs, WSL2, 3000 execs of /bin/true)
```
Workload slowdown (3000 execs):   -14.859%   (4.657s -> 3.965s)
Loader CPU idle:                0.000% of one core
Loader CPU under heavy load:    1.606% of one core
eBPF programs: 24383 events, average 6444.328 ns per event
Workload slowdown (3000 execs):   -5.113%   (4.146s -> 3.934s)
Loader CPU idle:                0.100% of one core
Loader CPU under heavy load:    1.213% of one core
eBPF programs: 36676 events, average 4418.065 ns per event
Workload slowdown (3000 execs):   -0.522%   (3.835s -> 3.815s)
Loader CPU idle:                0.000% of one core
Loader CPU under heavy load:    1.449% of one core
eBPF programs: 48969 events, average 3289.699 ns per event
```

An exec storm of 3000 processes is a worst case. Numbers are reported with the event rate, not as a single percentage.

## Dataset
- data/normal_train.jsonl and data/normal_val.jsonl (kept out of Git, backed up on D:)
- Baseline contains no ptrace and no mprotect events

## Learned
- A security tool must count its own dropped events
- Per-CPU maps avoid data races without atomics
- Anomaly detectors train on normal data only; train and validation are separate recordings
- Datasets must be clean: one wrong health-check wget would have polluted the baseline

## Problems solved
- Skipped patch (IPv6) caught by a build error; patches are now guarded and idempotent
- Manual two-window tests replaced by verify_all.sh

## Next week (Week 4)
- Container lifecycle events, filtering noise, Phase 1 demo, tag v1.0-phase1
