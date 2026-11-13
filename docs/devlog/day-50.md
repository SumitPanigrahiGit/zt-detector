# Day 50 - Verification covers Phase 2 and 3
- Added checks 14 (encoding at 10 s), 15 (replay reproduces Day 43), 16 (controller dry run flags the beacon, freezes nothing) to verify_all.sh
- Hypothesis written before running: all pass
- Full run (docs/results-day50-verify.txt):
    PASS: ptrace events captured
    PASS: W+X mprotect captured
    PASS: drop counter works (dropped=4585)
    PASS: zt-a and zt-b attributed correctly
    PASS: smoke test
    PASS: exit code 3 captured
    PASS: container start and stop recorded with name
    PASS: host events filtered in kernel (filtered=6017, dropped=0)
    PASS: latency measured (n=807 p50=63us p99=305us)
    PASS: attack demo: ptrace, W+X, shell and new destination all flagged
    PASS: graphs encoded, structural checks passed
    PASS: model trained, loss halved
    PASS: image recorded in lifecycle and exec events
    PASS: graphs encode
    PASS: replay matches Day 43
    PASS: dry run flags the beacon and freezes nothing
    ALL VERIFIED
- Caveats: check 16 is a single live run; checks 14 and 15 test reproducibility, not new behaviour
- Problems: earlier full runs were cut off (sudo credentials expired; setsid detached sudo from the terminal; duplicate runs overlapped); fixed by running one verification with one sudo keep-alive loop
- Next: FastAPI telemetry service
