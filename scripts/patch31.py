v = open("scripts/verify_all.sh").read()
if "12) model training" in v:
    raise SystemExit("already patched")
old = '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"'
assert v.count(old) == 1, "anchor not found"
check = '''echo "== 12) model training (Day 31) =="
.venv/bin/python ml/train.py > /tmp/zt_v12.txt 2>&1
grep -q "TRAIN OK" /tmp/zt_v12.txt && pass "model trained, loss halved" \\
  || fail "training failed (see /tmp/zt_v12.txt)"

'''
open("scripts/verify_all.sh", "w").write(v.replace(old, check + old))
print("patched")
