# Day 23 - Container start/stop tracking
- Loader polls the Docker cgroup directories every 100 ms (lifecycle_tick) and emits container_start / container_stop JSON events
- Containers already running at loader start are marked "preexisting":1
- Timestamps use CLOCK_MONOTONIC, the same time base as the kernel events
- Container names are now resolved when the container appears, not on its first event
- Added check 7 to verify_all.sh (start and stop recorded with name)
- Learned: polling is simple but gives a detection delay of up to about 100 ms; an inotify or Docker events watcher would be more precise
- Learned: an announced flag per cache entry is needed so stop is emitted only for containers that were announced
- Problems: none recorded
- Next: in-kernel container filter to cut noise
