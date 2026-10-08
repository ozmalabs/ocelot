# Live self-report lifecycle identity integration v1.4 amendment

The v1.3 capture passed its independent lifecycle/control gates and recorded matching lock, worker-start/end, and post-run source fingerprints. After that capture completed, `substrate/world_adapter.py` was edited again; current source SHA differs from the v1.3 lock and its modification time is later than the v1.3 raw-capture time. V1.3 therefore remains evidence for the exact earlier locked source state but is not a source-current confirmation.

V1.4 re-runs the unchanged protocol and gates against the current source state, with new lock/raw/analysis paths. Per-worker start/end and parent-end fingerprints remain required. The v1.3 evidence is preserved and not pooled with v1.4.
