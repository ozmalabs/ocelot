# CEGIS cross-task query-order v1 results

## Result

The source-locked 20-worker panel completed with zero worker failures. All 20 worker PIDs were unique. The independent analyzer passed all 147 checks for schedule/cell integrity, order, the fixed base-literal policy, query/row consistency, recorded native synthesis work, independent heldout labels, and heldout score flags.

| Task | Measure (median of five) | Ascending family | Seeded permutation |
|---|---|---:|---:|
| Triangular number | Counterexample rows | 2 | 1 |
|  | Total oracle calls | 21 | 17 |
|  | Candidates explored | 21,927 | 19,364 |
|  | Native synthesis time | 0.576 s | 0.402 s |
|  | Exact heldout workers | 5/5 | 5/5 |
| Population variance | Counterexample rows | 2 | 1 |
|  | Total oracle calls | 22 | 18 |
|  | Candidates explored | 2,813,270 | 2,774,268 |
|  | Native synthesis time | 118.24 s | 83.90 s |
|  | Exact heldout workers | 5/5 | 4/5 |

The selected query sequences differed in every pair for both tasks. All triangular workers converged on the same formula. For variance, the fixed-order arm returned the same correct variance expression in all five workers, although one worker exhausted the CEGIS rounds before its internal `converged` flag was set; all five still passed heldout. The seeded arm returned the same expression and passed heldout in four of five workers. The fifth did not find a final program within the registered search budget. This is a useful warning: fewer labels and a lower median cost did not preserve reliability on the harder task.

The benchmark wrapped numeric training labels in a float-convertible, non-numeric Python object before calling the unchanged native enumerator. This keeps the enumerator's literal set at `{-1,0,1,2}` and prevents query labels from changing the grammar. The wrapper and task sources are pinned in the lock. The oracle callback log records input values, not the returned labels; labels for the recorded inputs are deterministically reconstructable from the locked task oracle, and heldout labels were separately reconstructed in the analyzer. Future captures should also write each oracle response explicitly.

## Interpretation

Family order changes behavior across both scalar and list-statistic domains, so the single-task v1/v2 effect is not confined to triangular numbers. The size of the effect depends strongly on the task: triangular synthesis is cheap; variance search explores roughly 2.8 million candidates and takes 84–119 seconds median. Seeded ordering reduces query count and median work here, but one variance replicate fails to produce a solution, against 5/5 correct fixed-order heldout outcomes. Five pairs per task and one authored function per family do not support a general policy ranking. The data justify investing in a controlled query selector experiment and stronger resource/cap reporting, not adopting seeded permutations as the default.

## Artifacts

- Preregistration: `CEGIS_CROSS_TASK_QUERY_ORDER_V1_PREREG_20260930.md`
- Runner: `scripts/cegis_cross_task_query_order_v1.py`
- Analyzer: `scripts/analyze_cegis_cross_task_query_order_v1.py`
- Source lock: `evaluation/substrate_capability/cegis_cross_task_query_order_v1_20260930_lock.json`
- Raw capture: `evaluation/reports/cegis_cross_task_query_order_v1_20260930_raw.json`
- Analysis: `evaluation/reports/cegis_cross_task_query_order_v1_20260930_analysis.json`

Claim boundary: two authored task families, five paired order schedules each, and one host/source revision. This is evidence of order-sensitive CEGIS behavior, not autonomous hypothesis selection or natural-task prevalence.
