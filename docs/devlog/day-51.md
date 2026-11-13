# Day 51 - FastAPI telemetry service
- api/app.py: read-only /health, /events, /containers, /alerts plus POST /unfreeze/{name}; no freeze endpoint (freezing stays in the controller, dry-run default); binds 127.0.0.1; names validated by regex and must be a running container
- Hypothesis written before testing: reads under 100 ms on a 1 MB log; unfreeze returns a frozen container to frozen 0
- Test (docs/results-day51.txt):
    GET /health -> 200 0.026707
    GET /events -> 200 0.003314
    GET /containers -> 200 0.003329
    GET /alerts -> 200 0.002639
    before: frozen 1
    POST unfreeze -> {"name":"zt-api-t","frozen":0}
    after:  frozen 0
    bad name -> 404
    unknown -> 404
    API TEST DONE
- Notes: the encoded-path "bad name" test returned 404 (rejected by the router before validation); the validation branch was tested separately with names the router accepts; scale test used a synthetic log
- Caveats: no authentication (localhost only); one throwaway container; synthetic log for scale
- Problems: none recorded
- Next: SOC dashboard page served by the API
