# Day 29 - Process graph builder
- ml/graph_build.py turns JSON Lines events into one NetworkX multigraph per 10 s window
- Nodes: processes (pid@first-seen timestamp, so reused PIDs stay separate) and network destinations
- Edges: spawned (exec), connected, ptraced; exit events free the PID
- Node features so far: binary, uid, comm, counts of connect/mprotect/ptrace, W+X count
- Learned: a process tree is a graph; edge types are what an R-GCN needs
- Problems: none recorded
- Next: encode graphs as tensors and install PyTorch Geometric
