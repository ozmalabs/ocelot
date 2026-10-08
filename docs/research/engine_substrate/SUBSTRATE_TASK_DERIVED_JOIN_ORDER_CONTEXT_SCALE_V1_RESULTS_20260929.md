# Task-derived join-order context scale v1 results

## Result

The locked 216-worker replay completed with **3,247/3,247 independent checks
passing**. It crossed 0, 8, and 32 disconnected decoy goal/event components
with all 24 authored permutations of the production
`discourse_goal_select` four-edge match and three fresh-process replicates per
cell. Every worker retained the task and common-ground oracle, reached fixed
point at all ten event checkpoints, added the requested decoys, and left every
decoy Goal proposed. Per-clause native candidate counts conserved against
per-rule counts at every checkpoint. Within each decoy count, all 72 terminal
graph digests matched across permutations and repeats.

| Decoy components | Distinct installed orders | Candidate tests, min / median / max | Seed-authored request `0123` |
|---:|---:|---:|---:|
| 0 | 20 | 36 / 59 / 139 | 106 (order preserved) |
| 8 | 6 | 49 / 54 / 59 | 49 (`for_goal` moved first) |
| 32 | 6 | 49 / 54 / 59 | 49 (`for_goal` moved first) |

At 8 and 32 decoys the installer places `for_goal` first because its relation
has fewer graph edges than the other match relations at installation time.
This keeps the measured task work within 49–59 candidate tests across the
realized orders even as the decoy count quadruples from 8 to 32. The source
authored ordering costs 106 tests in the unaugmented graph, then is reordered
to a 49-test order in both augmented contexts. This is evidence that the
existing edge-cardinality heuristic can choose a useful order in this
controlled context; it is not a cost guarantee. At zero decoys its authored
order is unchanged and the 3.86× realized-order spread remains.

The pilot disclosed in the preregistration was exploratory and has no retained
worker-level raw records or source lock. Confirmatory conclusions above come
only from the separately locked fresh-process capture.

## Limits and next gate

This is one authored task, one rule, and synthetic disconnected distractors.
It does not measure natural-task prevalence, installer CPU/wall cost, or
uninstrumented latency. The repeated 49–59 work at 8 and 32 decoys is a
fixture-specific plateau, not an asymptotic result. Next measure installation
cost and total acquisition-plus-closure cost with instrumentation controls,
then repeat the native-order selection analysis on an independently authored
task/rule family with a different topology. Retain full semantic parity and
the per-clause work oracle.

## Artifacts

- [Preregistration](SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_task_derived_join_order_context_scale_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_join_order_context_scale_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_join_order_context_scale_v1_lock_20260929.json)
- [216-worker raw capture](../../../evaluation/reports/task_derived_join_order_context_scale_v1_raw_20260929.json)
- [Independent analysis](../../../evaluation/reports/task_derived_join_order_context_scale_v1_analysis_20260929.json)

Claim boundary: native candidate work with audit enabled on a controlled
context-scale intervention. No general optimizer, natural prevalence,
production identity, runtime-cost, or substrate-wide tractability claim follows.
