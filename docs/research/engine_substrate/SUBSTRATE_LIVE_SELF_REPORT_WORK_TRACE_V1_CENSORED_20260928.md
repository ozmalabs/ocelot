# Live self-report all-scope work trace v1: censored attempt

Date: 2026-09-28

The first three-worker capture is preserved at [raw attempt 1](../../../evaluation/reports/live_self_report_work_trace_v1_attempt1_censored_20260928.json) with its [pre-run lock](../../../evaluation/substrate_capability/live_self_report_work_trace_v1_attempt1_censored_lock_20260928.json). It is excluded from confirmatory evidence because the worker-0 start and end source locks differ: `domains/comprehend_text.py` changed from SHA-256 `e54db94b21df9c22cfa2cbb4b82ee221a2b98aa781478a22fd582a4fac427caa` to `bb146d677ef34d9ff44720488d1036ddeec75fbc009ff9b412f54717fa96cf4e`. Workers 1 and 2 ran after that change. Although all three returned the expected `self_report` then route-shortfall pattern, their evidence cannot be pooled under one source identity.

The initial lock also recursively hashed every JSON file below `seeds/`; it included 307,510 nested JSON files. Source inspection of `substrate/boot_all.py::_seed_manifest_paths` shows `load_all_seeds()` reads top-level `seeds/*.json` and direct `seeds/generated/*.json`, not the full nested tree. The v1.1 amendment changes the lock to match those loader inputs and makes the parent reject a worker whose starting source lock differs from the frozen lock. It preserves the task, metrics, and acceptance criteria.

No capability or counter-calibration claim is made from this attempt. The protocol amendment and clean rerun are linked from [v1.1 amendment](SUBSTRATE_LIVE_SELF_REPORT_WORK_TRACE_V1_1_AMENDMENT_20260928.md).
