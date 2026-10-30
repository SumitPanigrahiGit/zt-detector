# Day 12 - cgroup ID to Docker container ID
- Loader scans /sys/fs/cgroup/system.slice (docker-<id>.scope) and /sys/fs/cgroup/docker/<id>
- Directory inode = cgroup ID, so stat() gives the key to match kernel events
- Cache of 256 entries; rescans at most once per second on a miss, so host events stay cheap
- Output column CONTAINER shows the 12-char ID (matches docker ps) or "host"
- Learned: the kernel only knows cgroup IDs; names and IDs are resolved in user space
- Learned: cached IDs can go stale when a container is removed (to handle later)
- Problems: none recorded
- Next: show only container events, with container names
