# Day 01 - Environment Setup
- Windows + WSL2, Ubuntu 24.04 on D: drive, kernel 6.18, BTF present
- Installed clang 18, llvm, libbpf-dev, libelf-dev, build-essential, bpftool
- Generated vmlinux.h from kernel BTF
- Problems fixed: read-only disk on C: (moved Ubuntu to D:), apt HTTP mirror errors (switched to HTTPS)
- Lesson: wsl commands run in Windows cmd, everything else inside Ubuntu
- Next: first execve tracepoint
