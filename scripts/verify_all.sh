#!/bin/bash
# verify_all.sh - re-runs every feature test in one window
cd "$(dirname "$0")/.."
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
sudo mount -t bpf bpf /sys/fs/bpf 2>/dev/null
mkdir -p data docs
command -v strace > /dev/null || sudo apt install -y strace
FAIL=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }

start_loader() { sudo ./build/loader "$@" > /tmp/zt_v_out.txt 2>&1 & sleep 2; }
stop_loader()  { sudo pkill -INT -x loader; sleep 1.5; wait 2>/dev/null; }

echo "== 1) ptrace (Day 9) =="
sudo rm -f /tmp/zt_v1.jsonl
start_loader -q -j /tmp/zt_v1.jsonl
strace -e trace=none true 2> /dev/null
sleep 60 & SP=$!
sudo timeout 2 strace -p $SP -e trace=none > /dev/null 2>&1
kill $SP 2> /dev/null
sleep 1
stop_loader
grep -q '"type":"ptrace"' /tmp/zt_v1.jsonl && pass "ptrace events captured" || fail "no ptrace events"

echo "== 2) mprotect W+X (Day 10) =="
sudo rm -f /tmp/zt_v2.jsonl
start_loader -q -j /tmp/zt_v2.jsonl
python3 - << 'PY'
import ctypes
libc = ctypes.CDLL(None)
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_long]
libc.mprotect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
a = libc.mmap(None, 4096, 3, 0x22, -1, 0)
libc.mprotect(a, 4096, 7)
PY
sleep 1
stop_loader
grep '"type":"mprotect"' /tmp/zt_v2.jsonl | grep -q '"prot":7' \
  && pass "W+X mprotect captured" || fail "no W+X mprotect"

echo "== 3) dropped-event counter (Day 18) =="
sudo setsid ./build/loader -q > /tmp/zt_v_out.txt 2>&1 < /dev/null &
sleep 2
LP=$(pgrep -x loader | tail -1)
sudo kill -STOP "$LP"
( for i in $(seq 3000); do /bin/true; done ) < /dev/null
sudo kill -CONT "$LP"
sleep 2
stop_loader
D=$(grep "dropped events" /tmp/zt_v_out.txt | awk '{print $NF}')
[ "${D:-0}" -gt 0 ] && pass "drop counter works (dropped=$D)" || fail "drops not counted (got '${D}')"

echo "== 4) stale cache and container names (Day 14) =="
docker rm -f zt-a zt-b > /dev/null 2>&1
sudo rm -f /tmp/zt_v4.jsonl
start_loader -q -c -j /tmp/zt_v4.jsonl
docker run -d --name zt-a alpine sleep 600 > /dev/null
docker exec zt-a whoami > /dev/null
sleep 2
docker rm -f zt-a > /dev/null
docker run -d --name zt-b alpine sleep 600 > /dev/null
docker exec zt-b whoami > /dev/null
sleep 2
docker rm -f zt-b > /dev/null
sleep 1
stop_loader
A=0; B=0
sudo grep '"name":"zt-a"' /tmp/zt_v4.jsonl | grep -q whoami && A=1
sudo grep '"name":"zt-b"' /tmp/zt_v4.jsonl | grep -q whoami && B=1
[ "$A" = 1 ] && [ "$B" = 1 ] && pass "zt-a and zt-b attributed correctly" || fail "container names wrong"

echo "== 5) regression: smoke test =="
./scripts/smoke_test.sh | tail -1 | grep -q "ALL TESTS PASSED" \
  && pass "smoke test" || fail "smoke test"

echo
[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED" || { echo "SOME CHECKS FAILED"; exit 1; }

