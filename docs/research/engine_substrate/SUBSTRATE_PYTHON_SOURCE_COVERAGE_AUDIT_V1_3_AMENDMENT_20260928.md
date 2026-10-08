# Python source coverage audit v1.3 amendment

Date: 2026-09-28  
Status: preregistered current-source census refresh; execution has not started.

V1.2 remains preserved as the 69/833 coverage census for its source snapshot. After it completed, `substrate/world_adapter.py` changed during a live task-panel replay, censoring that task capture. V1.3 runs the unchanged deterministic Python/seed/map census against the now-current tree and records its own capability-map SHA-256, per-file source hashes, and pre/post stability gates. It does not reinterpret the censored v1.3 task workers or upgrade their partial outcomes.

The scan roots, static import resolution, literal profile-load extraction, seed-manifest scan, and coverage definitions are unchanged from v1.2. Any Python, seed, or capability-map drift during the census aborts. The purpose is to refresh source hashes and map coverage while live route measurement is deferred; source-link counts remain inventory metrics, not capability or test-coverage measures.
