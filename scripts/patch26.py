v = open("scripts/verify_all.sh").read()
if "10) attack demo" in v:
    raise SystemExit("already patched")
old = '[ "$FAIL" -eq 0 ] && echo "ALL VERIFIED"'
assert v.count(old) == 1, "anchor not found"
check = r'''echo "== 10) attack demo (Day 26) =="
./scripts/demo_attack.sh /tmp/zt_v10.jsonl > /tmp/zt_v10.txt 2>&1
ok10=1
for a in "ALERT ptrace" "ALERT wx-memory" "ALERT shell-spawn" "ALERT new-destination"; do
  grep -q "$a" /tmp/zt_v10.txt || ok10=0
done
[ "$ok10" = 1 ] && pass "attack demo: ptrace, W+X, shell and new destination all flagged" \
  || fail "attack demo missing alerts (see /tmp/zt_v10.txt)"

'''
open("scripts/verify_all.sh", "w").write(v.replace(old, check + old))
print("patched")
