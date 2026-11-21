# Day 56 - Whitepaper sections 1 to 3
- docs/WHITEPAPER.md: problem, design, implementation notes (descriptive; no measured figures yet)
- scripts/check_whitepaper.py: every number in the text must appear in docs/results-index.md or a small allow-list of design constants
- Caveats: the checker matches substrings, so a number could match by accident (for example 1 inside 10); it checks presence, not that the claim is right
- Problems: none recorded
- Next: section 4 (evaluation) with each number copied from the index
