# Day 19 - JSON Lines output
- Added -j FILE flag: one JSON object per event with raw fields plus syscall payload
- Hand-written JSON escaping; line-buffered output so tail -f works
- Validated: 14 lines, all valid JSON (12 exec, 2 connect), IPv6 and container rows correct
- Problems: build failed with "no member named daddr6" because Day 16 was not applied; fixed with guarded patch16b.py. Also ran commands from the wrong folder (/mnt/c) so the file looked missing
- Next: build a normal-behaviour dataset from nginx
