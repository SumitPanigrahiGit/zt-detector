# Day 18 - Dropped event counter
- Added a per-CPU array map "drops" incremented whenever bpf_ringbuf_reserve fails; loader sums it on exit
- Verified in verify_all.sh: loader frozen, 3000 execs, dropped = 1579 (buffer holds roughly 1500 events)
- Note: the forced-drop test was run during the Day 21 consolidation, not on Day 18 itself
- Learned: per-CPU maps avoid races without atomics; a security tool must report its own blind spots
