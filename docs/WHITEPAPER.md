# Runtime Container Anomaly Detection with eBPF and Graph Neural Networks

Status: a student project built and measured on one machine (WSL2, Ubuntu 24.04, kernel 6.18). Every measured figure below comes from `docs/results-index.md`.

## 1. Problem

Containers share the host kernel, so a compromised process inside one can attempt process injection, beaconing to unusual destinations, or abnormal process spawning. Signature-based tools miss behaviour they have no rule for. This project asks a narrower question: can a model trained only on a container's normal syscall behaviour flag deviations, and can the host contain the container quickly and reversibly?

The project does not claim to detect real exploits. All attacks are scripted simulations of the syscalls such an attack would make.

## 2. Design

1. **Tracing.** eBPF tracepoints on execve, connect (IPv4 and IPv6), ptrace, mprotect (only calls requesting execute permission) and process exit.
2. **Transport.** One ring buffer with a tagged-union event, so event order is kept across syscall types. A per-CPU counter records events lost when the buffer is full.
3. **Attribution.** The kernel knows only the cgroup ID. User space maps it to a container ID, name and image by scanning the Docker cgroup directories and reading Docker's metadata.
4. **Graphs.** Events are grouped into fixed windows per container. Nodes are processes and network destinations; edges are spawned, connected and ptraced relations.
5. **Model.** A two-layer relational graph convolutional autoencoder, trained only on normal windows. A window is flagged when its largest node reconstruction error exceeds a threshold.
6. **Containment.** A controller scores each completed window and, only when run with an explicit flag, freezes the container through its cgroup. Freezing is reversible.

## 3. Implementation notes

- **Fail-open kernel filter.** With the container-only flag, the kernel drops events only from cgroups the loader has confirmed to be host cgroups. Unknown cgroups still reach user space, so a new container's first events are not hidden. A fail-closed version hid them during development.
- **Per-regime thresholds.** Container startup windows score much higher than steady windows. One shared threshold was set by startup windows and made later attacks invisible, so startup and steady windows each get their own threshold (1.5 times the largest training score of that kind).
- **Container age from real start events.** The startup flag comes from the container's start event. A version based on position in the recording produced false positives on containers that were already running.
- **Per-image baselines.** A model trained on two services lost detection on one of them, so each image gets its own model. An image with no baseline is reported as unmonitored rather than as an attack.
- **Dry-run default.** The controller logs what it would freeze and acts only with an explicit flag.
- **Privilege.** The packaged loader runs privileged with host PID access. The API container is read-only and bound to localhost, with no authentication.

Measured results, with their caveats, are in section 4 and in `docs/results-index.md`.
