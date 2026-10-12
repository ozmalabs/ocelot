# Conversation task-scope parity pilot v1 results

Date: 2026-10-03

## Outcome

The source-locked runner and independent analyzer pass all gates on three fresh workers. Each worker runs the same authored two-concurrent-goal case from separate fresh monolithic and scoped worlds. Across three paired cases and 24 closure checkpoints per arm, every checkpoint graph digest, final graph digest, and goal-status vector matches. Both goals resolve in each run. The scoped arm uses a global resweep of the two task roots and ends each checkpoint with no progress or reported deferred effects.

The scoped route makes 44 scoped API calls per worker (132 total across the panel). Across 24 paired checkpoints, the descriptive median closure-call time is 0.044 ms for monolithic closure and 0.928 ms for the scoped route. The latter includes repeated scoped matching and per-scope delta/quiescence checks. The matcher still sees the full graph on each scoped call, so these measurements show the overhead of this conservative schedule on a tiny case; they do not estimate the payoff of a truly factored engine and must not be presented as a fair optimized speed comparison.

## Interpretation

This establishes a useful first result: current Microtheory-scoped closure can match full closure on one two-frame conversation fixture when task ownership edges are added symmetrically and every scope is repeatedly swept. It updates the API-fit finding: a prototype ownership encoding is possible with the existing API. The encoding uses unchecked `has_concept` edges because the loaded conversation vocabulary does not admit these task-specific memberships through ordinary validation. Frame discovery, ownership admission, optimized notification, and interface maintenance are not provided by this pilot.

### V1.1 quiescence evidence

V1.1 records both per-scope quiescence reports at each checkpoint. The independent analyzer confirms all 48 reports have zero progress and no pending deferred effects; each still says frame notifications are incomplete. The manual all-scope resweep continues until global quiescence. The v1.1 median checkpoint timings are 0.045 ms monolithic and 0.969 ms scoped under this harness, whose scoped timing includes repeated matching and explicit quiescence checks. See the [v1.1 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_1_AMENDMENT_20261003.md), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_20261003.json), and [analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_analysis_20261003.json).

The workload contains shared conversation state and goal/event cross-frame relations, but only one authored case and one frame count were evaluated. It does not establish general scheduler correctness, semantic completeness of observed accesses, safety under dynamic frame changes or deletions, high-coupling behavior, natural-task prevalence, or tractable scaling. The next gate is to broaden exact parity across common-ground stress and 4/8-goal cases; include dynamic owner updates, deletion/reuse and adversarial cross-frame dependencies; distinguish mutation/read coverage from full-graph matcher work; and account for all annotation and scheduling costs. A factorized implementation should not be proposed until those gates pass.

## Provenance

- [Method](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_METHOD_20261003.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_20261003.json)
- [Analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_analysis_20261003.json)
- [Preserved self-check failure](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_source_stability_failure_20261003.json)
- [V1.1 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1.py)
- [V1.1 analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_1.py)
- [V1.1 source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1_lock_20261003.json)
- [V1.1 capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_20261003.json)
- [V1.1 independent analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_analysis_20261003.json)
