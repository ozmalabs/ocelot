# Seed match-pattern census v1

Date: 2026-09-27 local

## Capture

The census reads each top-level `seeds/*.json` manifest once, hashes all input manifests, and inspects only each manifest's top-level `rules` collection. It records authored native match rows with at least three edge clauses and summarizes the variable-incidence projection. The capture covers 826 manifests and finds 900 multi-edge rules.

| Match edges | Rules |
|---:|---:|
| 3 | 405 |
| 4 | 219 |
| 5 | 119 |
| 6 | 71 |
| 7+ | 86 |

Of the 900 patterns, 864 are connected in the undirected endpoint-variable projection and 121 have a cycle in that projection. The largest multi-edge populations include `humanoid_adaptation` (96), `humanoid_developmental_curriculum` (87), and `embodied_development` (51). These counts describe seed-authored rule schemas, not the active or firing rule population in any task.

The frozen common-ground task's four lifecycle rules in `conversation_discourse_state.json` each have four match edges over four endpoint variables. They form a connected cyclic projection with repeated endpoints. This gives a task-family-specific candidate for the next native replay, alongside a higher-arity family for later coverage. The common-ground workload already has an independent identity oracle and repeatable fresh-process harness.

## Limits

This is a static manifest census. It does not establish which seeds load under a selected runtime profile, which rules fire, candidate-list sizes, candidate tests, or actual graph separators. Its endpoint-variable projection also ignores typed relation identity and predicate selectivity. Do not use the structural counts as runtime tractability evidence.

## Artifacts

- [Census script](../../../scripts/analyze_substrate_seed_join_shapes_v1.py)
- [Machine-readable capture and per-manifest input hashes](../../../evaluation/reports/substrate_seed_join_shapes_v1_20260927.json)
- [Common-ground task identity preregistration](SUBSTRATE_COMMON_GROUND_TASK_IDENTITY_REPLICATION_PREREG_20260926.md)
- [Common-ground task runner](../../../scripts/substrate_common_ground_task_identity_replication_v1.py)

Next: on the frozen common-ground task, capture the three discourse rules' installed match order and native candidate work by clause, then test a preregistered set of authored-order permutations. Require exact task, graph, and lifecycle parity before comparing work or timing. Treat the rule's existing global-cardinality reorder behavior as part of the baseline.
