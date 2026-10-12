# Common-ground stress Goal identity replication

## Result

The separately authored `phase3_common_ground_stress.v1` fixture has two same-recipient Goals, with intended sequences fixed by its ordering: Goal 0 owns selection/execution/result events 4/5/6 and Goal 1 owns 7/8/9. Nine locked fresh-process workers (three replicates × three rule arms) pass the independent analysis.

| Arm | Observed Goal 0 transitions | Observed Goal 1 transitions | Task oracle |
|---|---|---|---|
| Current temporal-only lifecycle rules | 4, 5, 6 | 4, 5, 6 | 0/3 pass |
| Addressee-guarded control | 4, 5, 6 | 4, 5, 6 | 0/3 pass |
| Explicit `event for_goal goal` links | 4, 5, 6 | 7, 8, 9 | 3/3 pass |

All event-level closures reach a fixed point, all three arms reproduce their final graph digest across replicates, and all arms preserve the fixture's expected CommonGround claims. Thus the error is specific to assignment of lifecycle transitions: the current rules close the second Goal during the first task's sequence, leaving the second sequence unassigned. Addressee identity cannot disambiguate the two tasks.

| Arm | Candidate pairs (median) | Term evaluations (median) | Closure wall time (median; range) |
|---|---:|---:|---:|
| Temporal | 150 | 516 | 0.277 ms (0.267–0.283) |
| Recipient guard | 153 | 576 | 0.285 ms (0.284–0.303) |
| Explicit identity | 144 | 408 | 0.296 ms (0.284–0.320) |

This is a correctness replication, not a speed result. Explicit `for_goal` links are supplied from the frozen fixture sequence in the candidate arm; the current production event path has not been shown to emit that relation for these lifecycle events. No production rule or source seed was changed.

## Reproducibility and next action

Protocol: [preregistration](SUBSTRATE_COMMON_GROUND_TASK_IDENTITY_REPLICATION_PREREG_20260926.md). Runner and independent analyzer: [runner](../../../scripts/substrate_common_ground_task_identity_replication_v1.py), [analyzer](../../../scripts/analyze_substrate_common_ground_task_identity_replication_v1.py). Locked inputs and evidence: [lock](../../../evaluation/substrate_capability/common_ground_task_identity_replication_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_common_ground_task_identity_replication_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_common_ground_task_identity_replication_v1_analysis_20260926.json).

Next, trace where the Phase 4A producer has an explicit Deliberation-to-Goal link but the discourse lifecycle event producer does not. Evaluate a production-safe way to carry task identity through selection/execution/result production, then require the explicit arm's oracle to pass without harness-authored identity edges. Keep this counterexample as a held-out regression family.
