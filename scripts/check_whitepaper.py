"""check_whitepaper.py - every number in the whitepaper must be in the results index or the allow-list."""
import re, sys
text = open("docs/WHITEPAPER.md").read()
index = open("docs/results-index.md").read()
# design constants and section numbers that are not measurements
ALLOW = {"1", "2", "3", "4", "5", "6", "10", "256", "1.5", "6.18", "24.04", "0"}
body = re.sub(r"`[^`]*`", " ", text)              # ignore code spans (file names)
body = re.sub(r"^#+ .*$", " ", body, flags=re.M)   # ignore headings
bad = []
for m in re.finditer(r"\d+(?:\.\d+)?", body):
    n = m.group()
    if n in ALLOW or n in index:
        continue
    bad.append(n)
print("numbers not in index or allow-list:", sorted(set(bad)))
sys.exit(1 if bad else 0)
