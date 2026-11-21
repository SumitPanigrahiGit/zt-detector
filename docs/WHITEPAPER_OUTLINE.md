# Whitepaper outline
1. Problem: detecting runtime hijack of containers (process injection, beaconing, rate anomalies) without signatures
2. Design: eBPF tracepoints -> one ring buffer -> container attribution -> process graphs -> R-GCN autoencoder -> reversible containment
3. Implementation notes: fail-open kernel filter, drop counter, per-regime thresholds, per-image baselines, dry-run default
4. Evaluation (each result: source file, counts, caveat)
   4.1 Tracing overhead and latency
   4.2 Detection on simulated attacks (beacon, scan, wx, burst)
   4.3 False positives and what caused them (startup windows, thin baselines, jitter)
   4.4 Cross-service behaviour (nginx vs redis vs python), poisoning
   4.5 Containment: freeze speed, end-to-end latency vs window size
5. Failed hypotheses (rule B, two-window rule at 10 s, 5 s windows, L=24 live)
6. Limitations: one machine (WSL2), simple workloads, scripted attacks, unseen-token crutch, poisoning only mitigated by review, privileged loader
7. Future work: real exploits, more workloads, temporal model, authentication
