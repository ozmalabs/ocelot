# Rule effect semantics contract

**Status:** source- and probe-backed behavioral contract for the native graph rule runner. This documents current semantics; it does not add truth maintenance or alter scheduler behavior.

## Contract

`run_rules` performs forward execution of graph effects. It reports whether an application changed the graph and schedules work according to the runner's dependency and invalidation policy. A reported fixed point means that the runner observed no eligible progress under that policy. It does **not** mean every derived fact still has an active justification, or that outputs equal a clean recomputation from current inputs.

| Effect behavior | Current contract |
|---|---|
| `AddEdge` | Inserts an edge, or updates attributes on the same `(source, type, target)` edge. A structural insertion or changed attributes count as progress. |
| `DelEdge` | Deletes the addressed edge when an executing match reaches the effect. It does not search for or retract other outputs whose conditions have become false. |
| `AddNode` / mint | Creates a fresh node for an executing application. Replaying an application can create another node; the runner does not infer that it replaces a previous minted result. |
| `DelNode` | Deletes the addressed node and its incident graph structure when an executing match reaches the effect. There is no automatic producer/justification cascade beyond that graph deletion. |
| Attribute writes and replacements | Apply when the corresponding effect executes. A later change to the input does not by itself undo or recompute an earlier output. |
| Rule invalidation | Re-execution is controlled by known read/write dependencies and scheduler policy. An unchanged terminal probe is scheduler-relative evidence, not a provenance audit. |
| Undo records | Support transactional rollback of an in-flight apply/compare operation. They are not retained as a persistent dependency ledger and do not provide truth maintenance after commit. |

Consequently, monotonic forward-chaining workloads can use closure as authored. A workload whose intended meaning includes withdrawal, replacement, or non-monotonic conditions must author those effects explicitly, or provide a separate support-maintenance/recompute layer. Callers that require the latter must validate the active derived state against an independent full recomputation oracle.

## Evidence and scope

The current native `EdgeData` records the edge triple; it does not retain rule-producer or justification metadata. `DelEdge` and `DelNode` are executed graph effects. The associated undo entries restore a tentative mutation during rollback and are consumed by that operation.

The effect-only attribute replay probe measured an edge update and fresh-node mint under full rescan: an existing edge was updated in place, while a second minted node was added and the stale first node remained. Its guarded-edge withdrawal control retained the old derived edge after the guard became false, including after forced rescan; a paired rule with explicit `DelEdge` removed it in both tested orders. Separate progress/rollback probes checked common native effects and a `ReplaceValue` collision. These are mechanism-level evidence for named effects and fixtures, not exhaustive validation of all effect sequences or host adapters. See [`SUBSTRATE_EFFECT_ONLY_ATTR_REPLAY_SAFETY_RESULTS.md`](SUBSTRATE_EFFECT_ONLY_ATTR_REPLAY_SAFETY_RESULTS.md), [`SUBSTRATE_EFFECT_PROGRESS_MATRIX_RESULTS.md`](SUBSTRATE_EFFECT_PROGRESS_MATRIX_RESULTS.md), and [`SUBSTRATE_REPLAY_ORDER_SCALE_RESULTS.md`](SUBSTRATE_REPLAY_ORDER_SCALE_RESULTS.md).

This contract applies to the inspected native graph/rule path. It does not define host-side domain adapter semantics, external effects, concurrent mutation, or all scheduling modes.

## Requirements for any replay or truth-maintenance change

Before replacing current suppression or adding selective replay, an implementation and its evaluation must:

1. Give every effect class an explicit replay policy, including whether repeated application is idempotent, replacing, deleting, or multiplicative.
2. Define how outputs unsupported by current matches are removed, including minted nodes and outputs shared by multiple justifications.
3. Reconcile progress accounting with exact before/after graph snapshots for every mutation class.
4. Compare incremental execution with a clean full recomputation oracle over bounded reference graphs and rule orders.
5. Test rollback, deletion, duplicate mint prevention, restart/resume, and scheduler residual state independently.
6. Keep resource budgets and fixed-point status distinct: a budget exit or quiescence under incomplete invalidation must not be presented as a semantically complete recomputation.

No engine behavior change is proposed by this contract. Its next use is as the acceptance boundary for the planned replay-safety and authored-workload locality experiments.
