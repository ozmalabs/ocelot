# Bounded three-edge join-order estimator v1 results

Date: 2026-09-27 local

## Result

The locked 126-worker panel passes all 1,120 independent analysis checks. Each of the six `(M, D/M)` graph settings has three fresh-process replicates across one RML count-order control, three other exact installed orders, and three sample budgets. Audit-on/off twins agree exactly; all arms reach the same terminal graph; native candidate counts are conserved across installed clauses; both deferred queues enqueue and drain exactly `M` times.

The simple capped estimator generally found the useful order, but its reliability depends on budget. Across 18 sampled cases per budget, B=8 selected an optimal order 13/18 times (72.2%), with 9.57× mean candidate-work regret and 19.2% mean relative prediction error. B=32 selected an optimum 17/18 times (94.4%), with 1.79× regret and 8.1% error. B=128 selected an optimum 18/18 times, with 1.00× regret and 3.6% error. Low-budget misses occurred in the sparse-path, high-decoy settings; sample estimates can miss rare successful partial bindings.

Exact native writer candidate work ranges by order from 48–1,216 for LMR, 288–70,784 for RML, and 528–1,254,464 for LRM/RLM across the panel. LMR is the minimum-work order in every setting. The B=128 estimator therefore identifies the optimum in this fixture, but it scores four orders and runs in Python. Median planning time is about 1.24 ms at B=128, 0.45 ms at B=32, and 0.22 ms at B=8; median Python allocation peaks are about 66.8 KB, 30.5 KB, and 14.4 KB respectively. End-to-end policy cost includes planner, writer installation, and plain closure; it is not evidence of a faster general optimizer. The process RSS measure is a process high-water mark and is not attributable to the planner alone.

## Interpretation and limits

This shows that bounded sampling can estimate and rank four orders for one deliberately structured three-edge chain, including when complete paths are sparse among equal-cardinality edge populations. It also shows the cost of robust sampling: increasing the budget improves selection and prediction while increasing planner time and allocation. Because LMR is always optimal in this construction, the panel does not demonstrate broad optimization generality, adaptive skip thresholds, a native implementation, or wins over the existing order. The repeated graph tables are retained in Python and the order estimator is a fixture-side diagnostic. The measured costs and accuracy do not transfer to arbitrary rules or natural task distributions.

The result supports a concrete next gate: replay the estimator and exact native counters on frozen, task-derived multi-edge rules, including varied join topology and cases where the optimum order changes. Before an engine change, measure total policy cost against the current installer and establish a skip threshold that avoids spending more than the estimated closure savings.

## Artifacts

- [Preregistration](SUBSTRATE_BOUNDED_THREE_EDGE_ORDER_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_bounded_three_edge_order_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_bounded_three_edge_order_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/bounded_three_edge_order_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_bounded_three_edge_order_v1_workers_raw_20260927.json)
- [Analysis](../../../evaluation/reports/substrate_bounded_three_edge_order_v1_analysis_20260927.json)

Claim boundary: one synthetic chain, four reachable connected orders, three fixed sample budgets, two multiplicities, three decoy ratios, and three process replications. No natural-workload tractability or general capability claim follows.
