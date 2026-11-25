# Zero-Trust Runtime Container Anomaly & eBPF Process Hijack Detector

eBPF syscall tracing, per-container process graphs, an R-GCN autoencoder trained on normal behaviour, and reversible containment (cgroup freeze, dry-run by default).

**Status:** v1.0, a student project measured on one machine (WSL2, Ubuntu 24.04, kernel 6.18).
**Not claimed:** detection of real exploits. All attacks are scripted simulations. Counts in `docs/results-index.md` are not rates.

Quick start: see "Run with Docker Compose" below. Full write-up: `docs/WHITEPAPER.md`. Re-test everything: `./scripts/verify_all.sh`.

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

## ML part (not included in a fresh clone)
Datasets (`data/`) and the virtualenv are git-ignored. To reproduce:
    python3 -m venv .venv && source .venv/bin/activate
    pip install networkx fastapi uvicorn
    pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install torch_geometric
    ./scripts/record_normal3.sh      # normal nginx recordings (about 22 min)
    ./scripts/stealth2.sh beacon 1   # attack recordings, see scripts/
