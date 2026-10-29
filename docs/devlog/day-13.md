# Day 13 - Container names and -c filter
- Container name read from /var/lib/docker/containers/<id>/config.v2.json (no docker CLI per event)
- Added NAME column and -c flag (container events only)
- Learned: user-space filtering is fine for low-volume events; high-volume ones should be filtered in the kernel
- Known limit: cache entries are not removed when a container is deleted (to fix next)
- Problems: (write any error and fix, or "none")
- Next: tests, cleanup, tag v0.2, week 2 summary
