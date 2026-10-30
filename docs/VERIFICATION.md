# Verification record

Some feature tests (ptrace, W+X mprotect, drop counter, container attribution, overhead benchmark)
were not run on the day each feature was written. They were run later, on 30 Oct 2026,
using scripts that are in this repository:

| Feature | Day built | How verified |
|---|---|---|
| execve, connect, IPv6 | 3, 8, 16 | smoke_test.sh and recorded datasets |
| ptrace | 9 | scripts/verify_all.sh check 1 |
| mprotect (W+X) | 10 | scripts/verify_all.sh check 2 |
| Container ID and name | 12, 13 | verify_all.sh check 4, smoke_test.sh |
| Drop counter | 18 | verify_all.sh check 3 (dropped = 1579) |
| Overhead | 17 | scripts/bench.sh, results in docs/bench-results.txt |
| JSON dataset | 19, 20 | validated with python json.loads; data/normal_*.jsonl |

Bugs found by this verification and fixed:
- New containers' first events were hidden by a 1-second rescan limit (now 20 ms)
- A missing IPv6 patch was caught by a build error

Re-run everything with: ./scripts/verify_all.sh and ./scripts/audit.sh
