#!/bin/bash
# mk_summary.sh - builds docs/week-03-summary.md using measured results
cd "$(dirname "$0")/.."
OUT=docs/week-03-summary.md
cat > "$OUT" << 'EOT'
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
EOT
echo '```' >> "$OUT"
grep -E "Workload slowdown|Loader CPU|eBPF programs" docs/bench-results.txt >> "$OUT"
echo '```' >> "$OUT"
cat >> "$OUT" << 'EOT'

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
EOT
echo "wrote $OUT"
cat "$OUT" | sed -n '12,22p'
