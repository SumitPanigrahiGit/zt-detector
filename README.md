# Zero-Trust Runtime Container Anomaly & eBPF Process Hijack Detector
eBPF syscall tracing + Graph Neural Network + automated container containment.

## Progress
Daily logs are in `docs/devlog/`.

## Tools
- `./scripts/verify_all.sh`  re-tests every feature in one command
- `./scripts/bench.sh`       measures overhead
- `./scripts/record.sh NAME SECONDS`  records a normal-behaviour dataset
- Loader flags: `-c` containers only, `-q` quiet, `-j FILE` JSON Lines output
