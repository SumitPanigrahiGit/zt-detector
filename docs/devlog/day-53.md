# Day 53 - Docker Compose packaging
- Dockerfile.api (python slim, user nobody), Dockerfile.loader (ubuntu:24.04 + libbpf1 libelf1 zlib1g libzstd1 + prebuilt build/loader), docker-compose.yml (loader privileged, pid host; api read-only, 127.0.0.1:8000, shared volume)
- Hypothesis written before testing: API works; loader may fail on WSL2
- Result: both services started; /health showed events_file true; after launching an alpine container from the host, /events returned its exec, exit and container_stop events and /containers listed it as stopped. Hypothesis about the loader failing was wrong
- Caveats: only tested on WSL2; the tool also lists its own containers; API read-only by design (no unfreeze in Compose); a fresh clone must run build.sh first; loader log was empty in quiet mode
- Problems: docker compose plugin was missing (installed docker-compose-v2); wc -l of the new files was not checked
- Next: end-to-end test from a fresh clone, then whitepaper
