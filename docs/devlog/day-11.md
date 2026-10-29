# Day 11 - Docker and container cgroup IDs
- Enabled systemd in WSL and installed docker.io
- Ran an alpine container and found its host PID via docker inspect
- Container cgroup ID (stat inode) differs from the host shell's
- Loader shows the container's cgroup ID for commands run with docker exec
- Learned: a container is a normal process tree on the host, isolated by namespaces and limited by cgroups
- Learned: the cgroup ID identifies the container for every process in it
- Problems: WSL had no systemd (PID 1 was init); enabled it in /etc/wsl.conf and restarted WSL from Windows cmd
- Next: map cgroup IDs to Docker container IDs automatically
