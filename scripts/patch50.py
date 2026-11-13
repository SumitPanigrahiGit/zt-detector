v = open("scripts/verify_all.sh").read()
if "14) encoding" in v:
    raise SystemExit("already patched")
old = '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"'
assert v.count(old) == 1, "anchor not found"
check = r'''echo "== 14) encoding at 10 s (Day 50) =="
ZT_WINDOW_S=10 .venv/bin/python ml/encode.py > /tmp/zt_v14.txt 2>&1
grep -q "ENCODE OK" /tmp/zt_v14.txt && pass "graphs encode" || fail "encoding (see /tmp/zt_v14.txt)"

echo "== 15) replay reproduces Day 43 (Day 50) =="
ZT_WINDOW_S=10 .venv/bin/python ml/replay_2win.py > /tmp/zt_v15.txt 2>&1
grep -q "normal windows: 132   flagged windows (act on 1): 0" /tmp/zt_v15.txt \
  && grep -q "beacon  recordings detected  act-on-1: 36 / 36" /tmp/zt_v15.txt \
  && grep -q "burst   recordings detected  act-on-1: 36 / 36" /tmp/zt_v15.txt \
  && pass "replay matches Day 43" || fail "replay differs (see /tmp/zt_v15.txt)"

echo "== 16) controller dry run (Day 50) =="
./scripts/live_test.sh dry > /tmp/zt_v16.txt 2>&1
grep -q "WOULD FREEZE zt-py" /tmp/zt_v16.txt \
  && ! grep -q "FROZEN" /tmp/zt_v16.txt \
  && grep -q "zt-py frozen state: frozen 0" /tmp/zt_v16.txt \
  && pass "dry run flags the beacon and freezes nothing" || fail "dry run (see /tmp/zt_v16.txt)"

'''
open("scripts/verify_all.sh", "w").write(v.replace(old, check + old))
print("patched")
