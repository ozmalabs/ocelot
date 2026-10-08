# Authored Bigville cut mutation follow-up preregistration

**Date:** 2026-09-26. **Parent protocol:**
[`SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md`](SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md).
This is a separately locked, Bigville-only mutation follow-up. It does not
replace the parent protocol's connected-dialogue mutation cell.

## Scope and frozen operations

Use the existing Bigville CAN builder, its 100 runtime-derived five-Concept
frames, and the active `can_native_update_3state` rule. Each worker constructs
a fresh substrate and first settles the no-injected-link baseline. Select the
`world_safe` Concepts in resident frames 0 and 1 as the fixed cross-frame edge
endpoints. Run these three independent branches:

1. **Insert:** insert both directed `causal_influence` edges at weight 0.2,
   then settle.
2. **Retract:** insert and settle the same pair at weight 0.2, remove both
   directions, then settle.
3. **Reweight:** insert and settle at 0.2, upsert the same directed edge keys
   at weight 0.35, then settle. Verify endpoint/type identity is unchanged.

For each branch, use separate fresh workers with runtime tracing disabled and
enabled. Store complete graph identity/type/attribute projections, full graph
digests, all causal dependencies, ownership, rule access declarations, trace
drop counts, full-closure reports, independent CAN residuals, and three
partition metrics at each post-operation checkpoint. Report `has_concept`
ownership links separately from task dependency edges; they define the frame
membership relation and are not counted as causal dependencies. Measure cut
rebuild CPU/wall time separately from substrate construction and closure.
Record whether the inserted/retracted/reweighted edge causes any rule progress
or closure graph change. If none occurs, the structural mutation cell passes
its capture/parity gates but is semantically insensitive and cannot support an
omission-divergence claim; do not tune endpoints after inspecting that result.

Compare authored ownership, balanced native-ID chunks with the same frame
sizes, and deterministic min-fill ordering on the union of every captured
non-ownership typed edge whose endpoints are task nodes and observed
task-to-task trace pairs. Report causal-influence crossings and all typed
crossings separately. Preserve unavailable fields as null. A partial trace
never removes an edge from the conservative dependency graph.

## Execution safety and claim boundary

The active rule's `reads_any` flag makes frame-local dependency completeness
unestablished. Therefore all three partitioned-execution arms must refuse
before scoped execution with the fixed reason `refused_wildcard_rule_access`.
Run monolithic full closure as the semantic oracle at every checkpoint. Do not
interpret the refusal as a partition parity pass or a speed result. Omitted
boundary execution is unsupported while every candidate partition refuses.

For the dialogue workload, record the mutation cell as
`unsupported_no_oracle_preserving_boundary_mutation_harness`. Retain the
existing connected-dialogue graph and shared-state evidence; do not substitute
a generated dialogue boundary for the authored workload.

This follow-up measures Bigville cut maintenance and the current safety
boundary only. It does not claim natural-task prevalence, all rule-effect
coverage, or general cheap-cut tractability.

## Outputs

Source/build lock, fresh-worker runner, independent analyzer, raw branches,
analysis, and a plan update. Preserve all first-attempt failures and keep the
parent protocol's unimplemented dialogue mutation gate open.
