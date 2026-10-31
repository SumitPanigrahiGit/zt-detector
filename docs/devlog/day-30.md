# Day 30 - Tensors and PyTorch Geometric
- Found the original training recording covered about 120 s, not 300 s; re-recorded train (600 s) and val (200 s)
- ml/encode.py: node features = one-hot program name or port (vocabulary from TRAIN only, 0 = unknown) plus is-network, root uid, log counts of connect/mprotect/ptrace, W+X flag
- Repeated edges are collapsed into one weighted edge per (src, dst, relation); relation ids: spawned 0, connected 1, ptraced 2
- Saved data/graphs.pt (train, val, attack) and data/vocab.json
- Added check 11 to verify_all.sh (encoding succeeds and structural asserts hold)
- Learned: the vocabulary must come from training data only; unknown programs map to index 0, which is exactly the signal for an unseen binary
- Known limits: small, uniform baseline; one workload type; the attack demo has a single window
- Problems: none recorded
- Next: R-GCN autoencoder and training loop
