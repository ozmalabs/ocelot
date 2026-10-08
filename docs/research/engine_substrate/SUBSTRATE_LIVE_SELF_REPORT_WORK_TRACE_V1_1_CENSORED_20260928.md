# Live self-report all-scope work trace v1.1: censored capture

Date: 2026-09-28

The manifest-aligned source-lock rerun is preserved in [raw v1.1 capture](../../../evaluation/reports/live_self_report_work_trace_v1_1_20260928.json) with its [frozen source lock](../../../evaluation/substrate_capability/live_self_report_work_trace_v1_1_lock_20260928.json), but is excluded from confirmatory evidence. Worker 0 matched the frozen lock. During worker 1, `substrate/world_adapter.py` changed from SHA-256 `88d504c82466e1b884ddfd38d5d7e04056fef79672794e99ee311073b91892eb` to `437a91c5482fca244d53404d0a48412dc4819a4bf29cca9bbb7927f21773c88b`; the runner preserved the two-worker prefix and stopped before worker 2.

Both captured workers report the expected successful self-report prompt followed by the known route-shortfall prompt, but this does not satisfy the three-worker preregistered gate. V1.2 therefore runs the unchanged workload from an isolated source snapshot whose hashes are verified against a stable double-read of the live worktree before measurement ([v1.2 amendment](SUBSTRATE_LIVE_SELF_REPORT_WORK_TRACE_V1_2_AMENDMENT_20260928.md)).
