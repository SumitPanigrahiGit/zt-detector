Phases 2 and 3 of my eBPF container-security project (simulated attacks, one WSL2 machine):

- Process graphs per 10 s window plus an R-GCN autoencoder trained only on normal behaviour.
- Bug found by testing: container-startup windows set the threshold and hid later attacks. Separate startup and steady thresholds fixed it.
- Containment by cgroup freeze: about 0.19 ms median for the write; end-to-end 2 to 10 s because the window length dominates.
- 5 s windows halved latency but flagged a normal container in 4 of 6 live runs. I kept that result in the write-up.
- Everything is re-testable with one script; failed hypotheses are documented.

GitHub: https://github.com/SumitPanigrahiGit/zt-detector
#eBPF #CloudSecurity #Linux #BuildInPublic
