# Day 20 - Normal-behaviour dataset
- scripts/gen_normal.sh: nginx proxy + nginx backend, steady traffic (5 req/s) plus periodic health-check execs
- Reason for two containers: static nginx makes almost no execve/connect; the proxy makes a connect() per request
- Recorded data/normal_train.jsonl (300 s, 574 events: 47 exec, 527 connect) and data/normal_val.jsonl (120 s)
- Baseline has no ptrace and no mprotect events
- Port 65535 connects come from the resolver probing IPv4/IPv6 and are normal
- Learned: anomaly detectors train on normal data only; train and validation are separate recordings
- Problems: health-check wget to localhost was refused (IPv6 ::1 vs IPv4-only nginx); switched to 127.0.0.1 and re-recorded so the data is clean
- Next: tag v0.3, Week 3 summary, LinkedIn post
