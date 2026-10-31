# Day 31 - R-GCN autoencoder
- ml/train.py: two RGCNConv layers (3 relation types) plus an MLP decoder reconstruct node features; trained on normal windows only, seed fixed; refuses to train on fewer than 20 train / 5 val windows
- Data: 62 train, 22 validation, 1 attack window; feature dim 26
- Loss 0.204 -> 0.0007; threshold 0.0499 (1.5 x max train window score, from train only)
- Validation: 0 of 22 windows flagged. Attack window max node error 0.2008 (flagged)
- Caveats: normal windows are almost identical (median error 0.0000), so zero false positives is a weak test; the attack uses an unseen binary, which hits the unknown-vocabulary column; one attack window only
- Problems: first run used a truncated paste and stale/tiny data (2 train, 0 val graphs); added a data-size guard
- Next: harder attacks using only known programs, and a fairer evaluation
