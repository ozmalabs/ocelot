# Same-addressee Goal identity scale extension v4.1 results

**Run:** 2026-09-26. **Grade:** 15 fresh workers at N=16, 32, and 64 Goals; locked extension of the earlier 2/4/8 diagnostic.

## Correctness

All size-specific gates pass. Explicit task links match the transition oracle; temporal-only and recipient-only controls misassign the same-addressee goals. Explicit-link owner-queue graphs exactly match full closure at all 64, 128, and 256 checkpoints. The owner report reaches each goal-origin frame at its result event. Omitting those notifications leaves receipts stale; a final global closure restores exact state. All scoped calls terminate without a progress-budget exit or deferred effect.

Across this extension, the owner queue preserves exact closure at 448/448 checkpoints. This is a useful correctness result for explicit owner IDs and `for_goal` links on the generated workload. It does not establish a production event schema or automatic scheduler.

## Operation counts and cost

From N=16 to N=64, a fourfold increase in goals and events produces about a 15.6× rise in explicit full-closure candidate pairs (7,544 → 117,728) and Terms (25,704 → 399,264). Doubling N from 16→32 and 32→64 raises these counts by 3.93× and 3.97×, close to quadratic growth for this workload over the measured range. The explicit owner queue rises similarly: 9,664→149,248 candidate pairs and 31,392→475,776 Terms. This is an empirical scaling pattern, not a formal complexity result.

At N=64, owner-queue work is 1.27× full closure in candidate pairs and 1.19× in Terms. Single-run accumulated wall time is 36.996 ms for the queue and 23.225 ms for full closure (1.59×). The v4 2/4/8 capture had larger wall ratios (2.35–2.41×), so the apparent decrease in overhead with scale needs repeated timing before interpretation. Peak RSS is 47.7 MiB full and 51.7 MiB queued at N=64, but the measure includes interpreter/native import and remains a high-water process measure, not graph-only allocation.

## Limits and next gate

The construction is generated, same-addressee, and supplies all task identity links. The scale points are single captures at three N values; they do not establish natural-task structure, a general polynomial bound, or an end-to-end product capability. The next step is an independently authored connected workload with task identity grounded in its real producer, followed by replicated timing and allocation-level memory measurement. See the [preregistration](SUBSTRATE_DISCOURSE_GOAL_IDENTITY_SCALE_V4_1_PREREG_20260926.md), [runner](../../../scripts/substrate_discourse_goal_identity_scale_v4_1.py), [independent analyzer](../../../scripts/analyze_substrate_discourse_goal_identity_scale_v4_1.py), [lock](../../../evaluation/substrate_capability/discourse_goal_identity_scale_v4_1_lock_20260926.json), [raw data](../../../evaluation/reports/substrate_discourse_goal_identity_scale_v4_1_20260926.json), and [analysis](../../../evaluation/reports/substrate_discourse_goal_identity_scale_v4_1_analysis_20260926.json).
