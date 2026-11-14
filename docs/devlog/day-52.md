# Day 52 - Dashboard
- api/dashboard.html (49 lines): one static page served at / by the API; polls /containers and /alerts every 2 s; Unfreeze button per frozen container; no freeze button; all text inserted with textContent because container names and alert lines come from untrusted containers
- Hypothesis written before testing: page loads, lists a throwaway container, shows it frozen, Unfreeze returns it to frozen 0
- Result: GET / returned 200; the page at localhost:8000 listed zt-dash and showed FROZEN with an Unfreeze button (screenshot taken); BEFORE CLICK frozen 1, AFTER CLICK frozen 0 (confirmed in cgroup.events)
- Caveats: one throwaway container; no controller running, so the alerts box was empty; no authentication (localhost only)
- Problems: the first two tests did not prove the click (state was frozen 0 before it); redone with before and after checks
- Next: Docker Compose packaging
