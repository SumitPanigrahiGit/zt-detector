# Zero-Trust Runtime Container Anomaly & eBPF Process Hijack Detector
eBPF syscall tracing + Graph Neural Network + automated container containment.

## Progress
Daily logs are in `docs/devlog/`.

## Tools
- `./scripts/verify_all.sh`  re-tests every feature in one command
- `./scripts/bench.sh`       measures overhead
- `./scripts/record.sh NAME SECONDS`  records a normal-behaviour dataset
- Loader flags: `-c` containers only, `-q` quiet, `-j FILE` JSON Lines output

## Documentation
- `docs/ARCHITECTURE.md`  components, data flow, limits
- `docs/VERIFICATION.md`  what was tested and when

## Run with Docker Compose
    ./scripts/build.sh            # build/ is git-ignored, so build the loader first
    sudo mount -t debugfs none /sys/kernel/debug; sudo mount -t bpf bpf /sys/fs/bpf
    sudo docker compose up -d --build
    curl http://127.0.0.1:8000/health      # dashboard: http://localhost:8000
    docker compose down

Security notes:
- The loader container runs `privileged: true` with `pid: host` (needed for eBPF). Run it only on machines you control.
- The API container is read-only, has no freeze or unfreeze endpoints, and is published on 127.0.0.1 only. Unfreeze is a host action (`api/app.py` run on the host).
- The API has no authentication.
- The controller is not part of Compose; it stays a manual, dry-run-by-default command.
- Tested only on WSL2 (Ubuntu 24.04, kernel 6.18).
