# Day 54 - Fresh-clone test
- Cloned the GitHub repo into /tmp/zt-fresh, ran build.sh, docker compose up, hit /health and /events
- Hypothesis written before testing: loader builds and Compose starts; ML scripts fail because data/ and .venv are not in Git
- Result: Compose built and started both services from the clone; /health returned events_file true; a host-launched alpine container produced exit and container_stop events through the API. data/ and .venv are absent from the clone, as predicted, so ML scripts need data recorded and a venv created
- Caveats: the build.sh output line was not captured; /events showed only 2 events (output was truncated with head -c 400); tested on the same WSL2 machine, not a different one
- Problems: none recorded
- Next: README for the ML part (venv, data recording), whitepaper
