# 60-second demo (throwaway containers only)
1. `./scripts/build.sh` then `sudo -v`
2. Dry run: `./scripts/live_test.sh dry`. Expect `WOULD FREEZE zt-py`, containers stay `frozen 0`.
3. Act run: `./scripts/live_test.sh act`. Expect `FROZEN zt-py`, then `frozen 1`; the script unfreezes before cleanup.
4. Dashboard: start the API (`sudo .venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000`), open http://localhost:8000.
Say out loud: the attack is simulated; the freeze write takes about 0.2 ms, but detection waits for the 10 s window.
