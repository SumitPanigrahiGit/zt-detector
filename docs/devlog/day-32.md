# Day 32 - Fairer evaluation
- Noisier baseline (gen_normal2.sh): normal2_train 4426 events, normal2_val 1909 events
- Four stealth attacks (stealth.sh): beacon, scan, burst, wx; ml/evaluate.py runs 3 seeds with the threshold from train data only
- Results (see docs/results-day32.txt): 0/26 validation false positives; beacon 2/2, scan 1/1, wx 1/1 flagged; burst missed (0/2): known programs and ports, only the rate differs
- Caveats: 1 to 2 attack windows per type, so no detection rate can be claimed; beacon and scan also hit unseen destination ports
- Problems: the first wx recording was empty (1 line) and showed as 0/0; redone (70 events) and a guard added so empty attacks fail loudly; interrupted runs left stray processes
- Next: add rate features to catch burst
