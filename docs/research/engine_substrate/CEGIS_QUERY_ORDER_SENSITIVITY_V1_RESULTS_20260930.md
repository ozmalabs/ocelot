# CEGIS query order sensitivity v1 results

## Result

The ten-worker source-locked panel completed with no worker failures. The independent analyzer passed all integrity checks: randomized schedule, exact cell coverage, unique fresh worker PIDs, fixed and permuted input orders, query/call reconciliation, row reconstruction, and heldout label/score reconstruction.

Changing only the supplied family order changed the selected query sequence in all five paired replicates. Ascending order selected `n=2,3,4` in every fixed-order worker; each seeded permutation selected a different two-query sequence. Both arms converged on `(n * ((n + 1) / 2))` in every worker and scored all six heldout values exactly (6/6).

| Measure, median across five paired runs | Ascending | Seeded permutation |
|---|---:|---:|
| Distinct counterexample rows added | 3 | 2 |
| Oracle calls on candidate-family values | 20 | 16 |
| Total oracle calls inside CEGIS | 26 | 21 |
| CEGIS wall time | 6.78 s | 3.35 s |

These cost differences are descriptive and must not be interpreted as a query-policy win. `domains.generator.synthesize` adds integer labels from observed outputs to its literal candidate set. Different query values therefore change both the specification and the search space; an early larger triangular-number label can expose a useful literal and alter synthesis work. This panel establishes order sensitivity and stable exact transfer on one task, but does not isolate information value from grammar/search effects, compare against an information-gain policy, or show general improvement from random order.

The current first-disagreement implementation also calls the oracle while scanning unselected family candidates. The capture logs those calls; the protocol did not seal labels. A follow-up should keep the query candidate pool and all allowed literals fixed independently of query labels, reveal only selected labels to the synthesis loop, and count/charge the sealed oracle calls. It should use multiple fresh functions before interpreting policy differences.

## Artifacts

- Preregistration: `CEGIS_QUERY_ORDER_SENSITIVITY_V1_PREREG_20260930.md`
- Runner: `scripts/cegis_query_order_sensitivity_v1.py`
- Analyzer: `scripts/analyze_cegis_query_order_sensitivity_v1.py`
- Source lock: `evaluation/substrate_capability/cegis_query_order_sensitivity_v1_20260930_lock.json`
- Raw capture: `evaluation/reports/cegis_query_order_sensitivity_v1_20260930_raw.json`
- Analysis: `evaluation/reports/cegis_query_order_sensitivity_v1_20260930_analysis.json`

This is a current-worktree, one-task capability probe. It is not a general active-learning or tractability result.
