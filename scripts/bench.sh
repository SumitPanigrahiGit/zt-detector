#!/bin/bash
# bench.sh - measures tracer overhead: idle CPU, CPU under load, per-event cost
cd "$(dirname "$0")/.."
N=${1:-3000}
TICK=$(getconf CLK_TCK)

now()   { date +%s.%N; }
ticks() { awk '{print $14+$15}' /proc/$1/stat; }      # utime + stime
calc()  { awk "BEGIN{printf \"%.3f\", $1}"; }

run_load() {
  local t0 t1
  t0=$(now)
  for ((i = 0; i < N; i++)); do /bin/true; done
  t1=$(now)
  calc "$t1 - $t0"
}

echo "== 1) Baseline: $N execs, no tracer =="
BASE=$(run_load)
echo "workload time: ${BASE}s"

sudo sysctl -qw kernel.bpf_stats_enabled=1
sudo ./build/loader -q $BENCH_FLAGS > /dev/null 2>&1 &
sleep 2
LPID=$(pgrep -nx loader)
if [ -z "$LPID" ]; then
  echo "loader is not running (is it built? did you mount debugfs/bpf?)"
  sudo sysctl -qw kernel.bpf_stats_enabled=0
  exit 1
fi

echo
echo "== 2) Idle: loader CPU for 10 s with no activity =="
T0=$(ticks "$LPID"); S0=$(now)
sleep 10
T1=$(ticks "$LPID"); S1=$(now)
IDLE=$(calc "($T1 - $T0) / $TICK / ($S1 - $S0) * 100")
echo "loader CPU while idle: ${IDLE}% of one core"

echo
echo "== 3) Load: same $N execs with tracer running =="
T0=$(ticks "$LPID"); S0=$(now)
TRACED=$(run_load)
sleep 1
T1=$(ticks "$LPID"); S1=$(now)
LOADCPU=$(calc "($T1 - $T0) / $TICK / ($S1 - $S0) * 100")
echo "workload time with tracer: ${TRACED}s"
echo "loader CPU under load: ${LOADCPU}% of one core"

# kernel-side program cost (sum over all trace_* programs)
read -r RT RC < <(sudo bpftool prog show | awk '/name trace_/ {
  for (i = 1; i <= NF; i++) {
    if ($i == "run_time_ns") t += $(i+1)
    if ($i == "run_cnt")     c += $(i+1)
  }
} END { print t+0, c+0 }')

sudo kill -INT "$LPID" 2>/dev/null
wait 2>/dev/null
sudo sysctl -qw kernel.bpf_stats_enabled=0

echo
echo "================ RESULTS ================"
SLOW=$(calc "($TRACED - $BASE) / $BASE * 100")
echo "Workload slowdown ($N execs):   ${SLOW}%   (${BASE}s -> ${TRACED}s)"
echo "Loader CPU idle:                ${IDLE}% of one core"
echo "Loader CPU under heavy load:    ${LOADCPU}% of one core"
if [ "$RC" -gt 0 ]; then
  AVG=$(calc "$RT / $RC")
  echo "eBPF programs: $RC events, average ${AVG} ns per event"
fi
echo "========================================="
