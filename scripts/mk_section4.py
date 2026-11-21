"""mk_section4.py - appends section 4 to docs/WHITEPAPER.md from docs/results-index.md."""
import re
idx = open("docs/results-index.md").read()
wp = open("docs/WHITEPAPER.md").read()
if "## 4. Evaluation" in wp:
    raise SystemExit("section 4 already present")
blocks = re.split(r"\n(?=## )", idx)[1:]
out = ["\n## 4. Evaluation\n",
       "Each entry shows its source file, status and caveat, followed by lines copied from that file. "
       "Counts are window or run counts, not rates. Seeds are not independent samples. "
       "Entries marked 'hypothesis failed' are results that contradicted what was expected before testing.\n"]
for b in blocks:
    out.append("### " + b.strip() + "\n")
open("docs/WHITEPAPER.md", "a").write("\n".join(out))
print("entries:", len(blocks))
