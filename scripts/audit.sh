#!/bin/bash
# audit.sh - checks that the repo really contains what the devlogs claim
cd "$(dirname "$0")/.."
FAIL=0
ok()  { echo "OK:   $1"; }
bad() { echo "GAP:  $1"; FAIL=1; }
chk() { [ -e "$1" ] && ok "$1" || bad "missing $1"; }

echo "== tools =="
for t in clang gcc bpftool docker git strace python3; do
  command -v $t > /dev/null && ok "$t installed" || bad "$t missing"
done
docker ps > /dev/null 2>&1 && ok "docker daemon reachable" || bad "docker daemon not reachable"
[ -s bpf/vmlinux.h ] && ok "vmlinux.h non-empty" || bad "vmlinux.h empty"

echo "== files =="
for f in bpf/hello.bpf.c bpf/execve.bpf.c bpf/common.h bpf/ringbuf.bpf.c src/loader.c \
         scripts/build.sh scripts/smoke_test.sh scripts/bench.sh scripts/gen_normal.sh \
         scripts/proxy.conf scripts/summarize.py scripts/verify_all.sh scripts/record.sh \
         docs/bench-results.txt docs/week-01-summary.md docs/week-02-summary.md \
         docs/week-03-summary.md data/normal_train.jsonl data/normal_val.jsonl; do
  chk "$f"
done

echo "== devlogs =="
for d in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21; do
  chk "docs/devlog/day-$d.md"
done

echo "== features really present in code =="
grep -q "sys_enter_execve"  bpf/ringbuf.bpf.c && ok "execve"   || bad "execve"
grep -q "sys_enter_connect" bpf/ringbuf.bpf.c && ok "connect"  || bad "connect"
grep -q "sys_enter_ptrace"  bpf/ringbuf.bpf.c && ok "ptrace"   || bad "ptrace"
grep -q "sys_enter_mprotect" bpf/ringbuf.bpf.c && ok "mprotect" || bad "mprotect"
grep -q "AF_INET6"          bpf/ringbuf.bpf.c && ok "IPv6"     || bad "IPv6"
grep -q "drops"             bpf/ringbuf.bpf.c && ok "drop counter" || bad "drop counter"
grep -q "write_json"        src/loader.c && ok "JSON output"   || bad "JSON output"
grep -q "record_stat"       src/loader.c && ok "stats"         || bad "stats"
grep -q "prune_cache"       src/loader.c && ok "cache pruning" || bad "cache pruning"

echo "== placeholders left in docs =="
if grep -rnE '\(write any error|[=:] X[ %,)]|X events|X ns|X%' docs/ ; then
  bad "placeholders above need real text"
else
  ok "no placeholders"
fi

echo "== git =="
git fetch -q
[ -z "$(git status --porcelain)" ] && ok "working tree clean" || bad "uncommitted changes"
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] && ok "local == GitHub" || bad "local differs from GitHub"
for t in v0.1 v0.2 v0.3; do
  git ls-remote --tags origin | grep -q "refs/tags/$t" && ok "tag $t on GitHub" || bad "tag $t missing on GitHub"
done

echo
[ "$FAIL" -eq 0 ] && echo "AUDIT CLEAN" || echo "GAPS FOUND (see GAP lines)"
