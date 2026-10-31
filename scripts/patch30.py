v = open("scripts/verify_all.sh").read()
if "11) graph encoding" in v:
    raise SystemExit("already patched")
old = '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"'
assert v.count(old) == 1, "anchor not found"
check = r'''echo "== 11) graph encoding (Day 30) =="
.venv/bin/python ml/encode.py > /tmp/zt_v11.txt 2>&1
grep -q "ENCODE OK" /tmp/zt_v11.txt && pass "graphs encoded, structural checks passed" \
  || fail "encoding failed (see /tmp/zt_v11.txt)"

'''
open("scripts/verify_all.sh", "w").write(v.replace(old, check + old))
print("patched")

