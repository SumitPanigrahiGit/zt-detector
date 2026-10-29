# Day 09 - ptrace tracing
- Added tracepoint sys_enter_ptrace (request + target pid)
- Loader decodes request numbers (TRACEME, ATTACH, SEIZE, POKETEXT, SETREGS...)
- Tested with strace (TRACEME) and strace -p (attach to a running process)
- Learned: ptrace is the debugger syscall and a classic process-injection primitive
- Learned: ATTACH/SEIZE on another PID plus POKETEXT/SETREGS is the suspicious pattern
- Problems: (write any error and fix, or "none")
- Next: mprotect tracing (executable memory)
