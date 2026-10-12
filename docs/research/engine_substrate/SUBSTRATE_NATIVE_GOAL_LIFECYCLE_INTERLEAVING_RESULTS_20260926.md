# Native Goal lifecycle interleaving results — pre-fix diagnostic

This document records the v1 capture before the native uniqueness guard. The issue below was corrected and re-confirmed in [v1.1 results](SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_V1_1_RESULTS_20260926.md); use v1.1 for current behavior.

## Findings

Three source-stable fresh full-seed processes pass the six-checkpoint interleaving oracle for two simultaneously active Goals: A selection, B selection, B execution, A execution, A result, B result. Each explicit event-to-Goal link produces the expected per-Goal transitions, and both Goals end resolved, closed, and absent from the active set.

A missing-owner selection event transitions neither Goal. The ambiguous-owner diagnostic exposes a gap: when one selection event has `for_goal` edges to both Goals, the native rules select both Goals. This happens in all three workers. The event payload's declared target does not constrain the native rules; every matched owner edge is treated as authority. Therefore the current native lifecycle has a useful omission guard but no uniqueness guard for explicit ownership.

The capture is valid: three distinct PIDs, six complete checkpoints each, source fingerprints stable at worker start/end and post-run, and independent analysis verifies the raw lock and all semantic observations. The positive interleaving result is fixture-level explicit-owner behavior, not thread concurrency or a production scheduler claim.

## Tractability/capability implication

The task identity representation is sufficient when the graph contains exactly one `for_goal` owner edge. Native transition matching alone does not enforce the single-owner invariant. That invariant needs to be encoded either in the graph API that creates lifecycle events and/or in the transition rules so malformed multi-owner events fail closed. The immediate design is a native guard that suppresses transitions whenever an event has any `for_goal` neighbor other than the matched Goal, with the interleaved positive and ambiguous-owner controls retained as regressions.

## Artifacts

- Preregistration: [`SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_PREREG_20260926.md`](SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_PREREG_20260926.md)
- Runner: [`substrate_native_goal_lifecycle_interleaving_v1.py`](../../../scripts/substrate_native_goal_lifecycle_interleaving_v1.py)
- Independent analyzer: [`analyze_substrate_native_goal_lifecycle_interleaving_v1.py`](../../../scripts/analyze_substrate_native_goal_lifecycle_interleaving_v1.py)
- Lock: [`native_goal_lifecycle_interleaving_v1_lock_20260926.json`](../../../evaluation/substrate_capability/native_goal_lifecycle_interleaving_v1_lock_20260926.json)
- Raw capture: [`substrate_native_goal_lifecycle_interleaving_v1_20260926.json`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_20260926.json)
- Independent analysis: [`substrate_native_goal_lifecycle_interleaving_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_analysis_20260926.json)
