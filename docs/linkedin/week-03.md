Week 3 update: eBPF Container Security Detector

This week was about trusting the tool:
- Measured overhead: loader CPU and per-event kernel cost, reported with the event rate (3000 execs/run worst case)
- Added a dropped-event counter, so the tracer reports when it was blind
- IPv6 connect tracing, JSON Lines export
- Recorded a clean "normal behaviour" dataset from an nginx proxy and backend

Biggest lesson: one health check that failed would have put abnormal events into my "normal" data. Clean baselines matter more than big ones.

Next: finishing Phase 1, then process graphs and the GNN.

GitHub: https://github.com/SumitPanigrahiGit/zt-detector

#eBPF #CloudSecurity #Docker #Linux #BuildInPublic
