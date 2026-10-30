# Day 22 - Process-exit events
- Added tracepoint sched_process_exit, reported only for the thread group leader (tid == tgid)
- exit_code read with BPF_CORE_READ(task, exit_code); loader decodes status (>>8) and signal (&0x7f)
- New event type EVT_EXIT; JSON output has exit_code and signal
- Added check 6 to verify_all.sh: sh -c 'exit 3' must produce exit_code 3
- Learned: sched_process_exit fires per thread, so filtering on tid == tgid avoids duplicate events
- Learned: exits are needed in the process tree so reused PIDs are not confused
- Problems: none recorded
- Next: container start/stop tracking
