# Day 16 - IPv6 connect
- Added daddr6[16] to the connect payload and an AF_INET6 branch in trace_connect
- sockaddr_in6 read by offsets (port at +2, address at +8), all user reads before ringbuf reserve
- Unused union fields are zeroed so user space never sees stale bytes
- Loader prints [addr]:port for IPv6 using inet_ntop(AF_INET6)
- Learned: read user memory into locals first, then reserve, so there is nothing to discard on failure
- Problems: (write any error and fix, or "none")
- Next: measure overhead and count dropped events
