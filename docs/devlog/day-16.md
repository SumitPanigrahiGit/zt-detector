# Day 16 - IPv6 connect
- Added daddr6[16] to the connect payload and an AF_INET6 branch in trace_connect
- sockaddr_in6 read by offsets (port at +2, address at +8); all user reads happen before ringbuf reserve
- Loader prints [addr]:port for IPv6
- Applied late (during Day 19) because the first patch was skipped
- Learned: patches must be idempotent and anchored precisely
