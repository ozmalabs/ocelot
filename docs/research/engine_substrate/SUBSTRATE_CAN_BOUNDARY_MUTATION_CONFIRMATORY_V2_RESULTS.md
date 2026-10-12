# CAN boundary mutation confirmation v2

**Run:** 2026-09-25. **Evidence grade:** preregistered synthetic mechanism confirmation. **Runner:** [`substrate_can_boundary_mutation_confirmatory_v2.py`](../../../scripts/substrate_can_boundary_mutation_confirmatory_v2.py). **Independent analyzer:** [`analyze_substrate_can_boundary_mutation_confirmatory_v2.py`](../../../scripts/analyze_substrate_can_boundary_mutation_confirmatory_v2.py).

The protocol was frozen before the run in [`SUBSTRATE_CAN_BOUNDARY_MUTATION_CONFIRMATORY_PREREG_20260925.md`](SUBSTRATE_CAN_BOUNDARY_MUTATION_CONFIRMATORY_PREREG_20260925.md) and [`can_boundary_mutation_confirmatory_v2_lock_20260925.json`](../../../evaluation/substrate_capability/can_boundary_mutation_confirmatory_v2_lock_20260925.json). It uses the authored `can_native_update_3state` rule and three independently seeded path fixture parameterizations (20260925, 8675309, 104729), at N=8/16/32 with four-node frames. Each seed/size pair covers eight mutations: edge insertion, deletion and replacement; external and identity field writes; one node birth; one boundary-adjacent node deletion; and a mixed weight-plus-field write. The v1.1 event-settlement mechanism was reused unchanged; only the initial fixture parameter generator was replaced.

## Result

All 72 event/reference pairs settled under the 100,000 progress cap, matched active-node/state projections, and passed an independently recomputed zero-residual check. All nine preregistered omitted-notification controls (insertion, birth, deletion at N=8 for each seed) disagreed with the reference and had positive independently recomputed residuals. The analyzer verified the exact seed/size/mutation set, runner/base-runner/analyzer/protocol/seed/native-extension hashes, and current-source engine provenance (`source_match=own`, no stale Rust files).

Progress applications were equal between event and full-rescan arms in all 72 cases. No wall time, allocations, candidate work, or frame visits were measured. Thus this confirms propagation correctness for these seeded fixtures; it establishes no reduction in work or cost advantage.

Raw records are [`substrate_can_boundary_mutation_confirmatory_v2_20260925.json`](../../../evaluation/reports/substrate_can_boundary_mutation_confirmatory_v2_20260925.json), and independent analysis is [`substrate_can_boundary_mutation_confirmatory_v2_analysis_20260925.json`](../../../evaluation/reports/substrate_can_boundary_mutation_confirmatory_v2_analysis_20260925.json).

## Claim boundary and next gate

The event runner still receives the affected-frame set from its caller and uses the same native scoped-settlement implementation as the full-scan reference. The fixtures are sparse paths with fixed contiguous frames and one local update rule. The three seeds vary fields and non-target path weights; they do not vary topology, frame construction, or rule family. Each cell contains one birth or one deletion, not a sequence of repeated lifecycle operations. No authored task trace, discovered partition, automatic native effect-to-frame notification, arbitrary dependency graph, minting/idempotence behavior, or production GALS is tested.

Next use a frozen task-derived CAN scenario or rule trace and runtime-derived access partitions to test repeated lifecycle changes and notification completeness. Measure frame visits, candidate work, partition maintenance, batching, and memory against a semantically complete full-rescan reference. Keep `can_native_note_coactivation`/`AddNode` mint idempotence as a separate full-closure gate; the measured update matrix is `SetAttr`-only. Do not turn equal-progress parity into a speed claim.
