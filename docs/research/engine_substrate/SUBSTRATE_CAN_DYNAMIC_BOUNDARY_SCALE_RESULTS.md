# CAN dynamic boundary wakeup scale pilot

**Run:** 2026-09-25. **Evidence grade:** pre-locked mechanism scale pilot. **Runner:** [`substrate_can_dynamic_boundary_scale.py`](../../../scripts/substrate_can_dynamic_boundary_scale.py). **Independent analyzer:** [`analyze_substrate_can_dynamic_boundary_scale.py`](../../../scripts/analyze_substrate_can_dynamic_boundary_scale.py).

**Protocol and amendment:** [`SUBSTRATE_CAN_DYNAMIC_BOUNDARY_SCALE_PREREG_20260925.md`](SUBSTRATE_CAN_DYNAMIC_BOUNDARY_SCALE_PREREG_20260925.md), with adapter-only correction in [`SUBSTRATE_CAN_DYNAMIC_BOUNDARY_SCALE_AMENDMENT_20260925.md`](SUBSTRATE_CAN_DYNAMIC_BOUNDARY_SCALE_AMENDMENT_20260925.md). **Lock:** [`can_dynamic_boundary_scale_v1_1_lock_20260925.json`](../../../evaluation/substrate_capability/can_dynamic_boundary_scale_v1_1_lock_20260925.json). The failed pre-amendment attempt is preserved at [`substrate_can_dynamic_boundary_scale_attempt_v1_20260925.json`](../../../evaluation/reports/substrate_can_dynamic_boundary_scale_attempt_v1_20260925.json).

## Result

The locked run covered 16 deterministic cells: N=8/16/32/64, four-node frames, and cross-frame edge insertion, edge deletion, edge-weight replacement, or an external-field change. Every mutation changed the state. The event queue and full round-robin rescan produced identical final state vectors in 16/16 cells, and an independent post-run evaluator recomputed zero CAN residuals for both arms in every cell. All 16 arms completed under the 100,000-progress cap. The no-initial-notification edge-insertion control remained detectably stale with positive residual at each size (4/4).

| N | Frames | Insert steps / event turns | Delete steps / turns | Weight replacement steps / turns | Field change steps / turns |
|---:|---:|---:|---:|---:|---:|
| 8 | 2 | 1 / 3 | 1 / 2 | 4 / 5 | 1 / 2 |
| 16 | 4 | 1 / 4 | 1 / 3 | 4 / 7 | 1 / 2 |
| 32 | 8 | 1 / 4 | 1 / 3 | 4 / 7 | 1 / 2 |
| 64 | 16 | 1 / 4 | 1 / 3 | 4 / 7 | 1 / 2 |

Progress-application counts matched exactly between event and full-rescan arms in every cell. Event turns report how many scoped frames the Python event queue processed; the harness did not count full-rescan frame turns, so this result does not show a work reduction. No wall-time or allocation measurements were collected.

The independent analyzer verifies all registered size/mutation pairs, lock-to-runner/seed/extension hashes, current engine source match (`own`, no stale Rust files), exact state parity, and recomputed per-node residuals. Raw execution data are in [`substrate_can_dynamic_boundary_scale_20260925.json`](../../../evaluation/reports/substrate_can_dynamic_boundary_scale_20260925.json); independent checks are in [`substrate_can_dynamic_boundary_scale_analysis_20260925.json`](../../../evaluation/reports/substrate_can_dynamic_boundary_scale_analysis_20260925.json).

## Claim boundary and next gate

This is scale evidence for one caller-notified event-propagation mechanism on a path-shaped, authored CAN model with one 3-state rule. Initial affected frames are supplied explicitly by the caller. It does not test automatic native effect-to-frame notification, node birth/deletion, multiple rule families, natural task locality, alternate topologies, or a hierarchy discovered from access traces. The event and reference arms share the same native scoped settlement implementation; their independent agreement checks the queue's propagation against full scans, not against a separate engine.

Next, include node creation/deletion and mixed edge/attribute effects in bounded probes, then instrument native writer-to-frame notification and compare it with explicit full recomputation. Retain dense/high-coupling controls and measure partition/update overhead before making a GALS or general cheap-cut claim.
