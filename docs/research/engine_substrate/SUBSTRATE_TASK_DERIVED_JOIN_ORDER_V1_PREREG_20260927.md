# Task-derived four-edge join-order replay v1 preregistration

Date: 2026-09-27 local

## Question

On a frozen common-ground conversational task, how much does the current native matcher’s candidate work vary when the authored order of a real four-edge rule changes, and which installed orders does the existing `add_rule` reorderer realize?

## Fixture and arms

Use the frozen `phase3_common_ground_stress.json` task and `conversation_discourse_state.json` rules through the existing task identity replication harness. Preserve the seed’s four match clauses for `discourse_goal_select`; vary all 24 authored permutations of those four clauses. Explicit `event for_goal goal` graph links are fixture supplied to support the independent task oracle; no extra duplicate rule clause is appended. Reinstall the three lifecycle rules with unchanged predicates/effects and capture the installed `discourse_goal_select` order from `export_rules()`. Run three fresh processes per permutation (72 workers total), in a seeded shuffled order.

The harness runs ten event closures per worker. Audit-off/on is not crossed here: native global, per-rule, and per-clause counters are enabled so the target writer’s matcher work can be attributed. The independent task oracle, common-ground oracle, fixed-point status, and final graph digest are the semantic gates. Record target-rule candidate tests by installed clause, total candidate tests over the ten closures, closure CPU/wall time, candidate enumerations, candidate rejections, and term-evaluation totals. Timings are secondary because the opt-in counters add overhead.

## Admission gates

- Exactly 72 unique `(permutation, replicate)` workers with unique PIDs and stable source/native inputs.
- Every permutation installs the read-back order associated with its requested author order; no assumed mapping from author to installed order.
- Every worker passes task and common-ground oracles, all ten closures reach fixed point, and all 72 terminal graph digests agree.
- For each checkpoint, target-rule clause candidate counts sum to its target-rule candidate-test counter; total work equals the sum across all ten checkpoints.
- Report selection/work differences by installed order and replicate; no minimum effect or significance threshold is required.

## Scope boundary

This is a frozen, task-derived workload with fixture-supplied identity links, one varied lifecycle rule, one task family, and opt-in audit. It measures actual native candidate work and order sensitivity, not automatic order learning, natural prevalence, uninstrumented latency, or general tractability. The source seed is currently a dirty-worktree input, so its exact bytes and the native binary are locked for this run.
