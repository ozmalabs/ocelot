# Task-derived anaphora join-order estimator v1.3 results (2026-09-29)

## Result

The current-source panel completed all 174 declared workers. The independent analyzer passes **472/472 checks**, including complete source-order plus 24-request coverage, native order readback, candidate-counter conservation, exact task output, fixed points, sorted whole-graph parity, 174 unique worker processes, hashed logs, and source/native stability. V1 and v1.1 harness attempts and the v1.2 order-sensitive digest capture are preserved separately and excluded; v1.3's graph digest sorts nodes and edges before hashing.

The native installer already performs a greedy cost-based match-edge reorder in `Substrate::add_rule`: it reads live edge-type cardinalities, picks a low-cardinality first edge, then extends through connected clauses while preferring low-cardinality relations ([implementation](../../../runners/dsl/src/substrate.rs), [reorder algorithm](../../../runners/dsl/src/rewrite.rs)). The measured requested-to-installed map is this existing behavior, not a new optimization introduced by the sampler. It substantially narrows the available order set as the context graph grows. Including the untouched source order, D=0 has five realized orders: candidate tests are 13 (source), 10, 12, 15, and 16. At D=2, the 24 requested permutations all realize one reordered order with 28 candidate tests, compared with 25 for the untouched source order. At D=4, they again collapse to one reordered order with 28 tests, compared with 37 for source order. Replicates reproduce the same values. Thus the sampler improves this fixture at D=0 and D=4, but picks a 12%-higher-work order than source at D=2; at D=2/4 it cannot choose among the requested alternatives because the installer maps all of them to one order.

| Context distractors | Distinct installed orders, including source | Source candidate tests | Selected candidate tests (B=8/32/128) | Selection regret vs best realized order |
|---:|---:|---:|---:|---:|
| 0 | 5 | 13 | 10 | 1.00× |
| 2 | 2 | 25 | 28 | 1.12× |
| 4 | 2 | 37 | 28 | 1.00× |

All three budgets choose the same order in all six task/replicate cells: **4/6** selections attain the minimum measured candidate work, median regret is 1.00×, and maximum regret is 1.12×. Raising B from 8 to 128 does not improve this result on these cells.

The candidate-work reductions do not repay planning cost on these tiny closures. Across the six paired cells, `planning wall + order installation + plain closure` is never below source-order plain closure. Median combined/source ratios are **19.20× at B=8, 22.68× at B=32, and 20.23× at B=128**. For example, at D=0 the selected arm reduces target candidate tests 13→10, while planning and installation alone take roughly 1.5 ms against about 0.08 ms for source-order closure. These CPU timings are fixture-scale and do not extrapolate to larger joins; the measured policy is nevertheless a loss on every tested cell.

## Interpretation

This is a negative result for applying the bounded sampler to this task/rule/graph-size envelope. It verifies that the estimator ranks some orders well against exact native counters, and also shows that native installation canonicalization can collapse distinct requests, that source order can beat every reordered arm, and that planner plus installation overhead dominates when the closure is already cheap. No production reordering is justified. The D=2 miss also shows that relation cardinality alone is not a reliable proxy for this rule’s joined candidate work. A useful next gate must compare the native greedy order with exact work on larger candidate populations, include rule-installation timing, and demonstrate amortized savings on more than one task-derived family.

## Reproduction and artifacts

- [V1.2 preregistration](SUBSTRATE_TASK_DERIVED_ANAPHORA_ORDER_ESTIMATOR_V1_2_PREREG_20260929.md)
- [V1.3 amendment](SUBSTRATE_TASK_DERIVED_ANAPHORA_ORDER_ESTIMATOR_V1_3_AMENDMENT_20260929.md)
- [Runner](../../../scripts/substrate_task_derived_anaphora_order_estimator_v1_3.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_anaphora_order_estimator_v1_3.py)
- [Source/native lock](../../../evaluation/substrate_capability/anaphora_order_estimator_v1_3_lock_20260929.json)
- [Raw workers](../../../evaluation/reports/anaphora_order_estimator_v1_3_raw_20260929.json)
- [Analysis](../../../evaluation/reports/anaphora_order_estimator_v1_3_analysis_20260929.json)
- [Run manifest and child-log hashes](../../../evaluation/reports/anaphora_order_estimator_v1_3_20260929.json)
- [Excluded v1 request-index attempt](../../../evaluation/reports/anaphora_order_estimator_v1_harness_attempt1_raw_20260929.json)
- [Excluded v1.1 context-map attempt](../../../evaluation/reports/anaphora_order_estimator_v1_1_harness_attempt1_raw_20260929.json)
- [Excluded v1.2 order-sensitive digest capture](../../../evaluation/reports/anaphora_order_estimator_v1_2_harness_attempt1_raw_20260929.json)

Claim boundary: one authored four-edge anaphora rule, three generated context sizes, two process replicates, 24 requested permutations, and one sampled planner. No natural task prevalence, general optimizer, or production integration claim follows.
