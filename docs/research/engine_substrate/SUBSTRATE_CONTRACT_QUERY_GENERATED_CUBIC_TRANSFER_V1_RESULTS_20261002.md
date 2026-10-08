# Generated cubic pool lazy-query transfer v1 — results

## Result

The three-worker source/native-locked panel completed with zero independent analyzer errors. Each fresh worker generated a complete pool of 10 behaviorally distinct Terms after exploring 945 candidates; at least one pool member matched the cubic target on all five held-out inputs. Both uncached and lazy-matrix arms selected the same single query, `x=-4`, retained the same correct survivor, and predicted all held-outs exactly. Query labels, entropy, predictions, terminal states, and survivor traces matched exactly across arms.

## Cost

| Measure | Median |
|---|---:|
| Pool generation | 49.39 ms |
| Queries | 1 |
| Uncached selector | 0.710 ms; 160 native evaluations |
| Lazy-matrix selector | 0.694 ms; 130 matrix cells/evaluations |
| Native evaluation reduction | 18.75% |

The wall-time difference is small at this workload size. Pool generation dominates selection, so no end-to-end learner speedup is established.

## Interpretation and limits

This extends exact query/survivor parity and held-out correctness to a cubic hypothesis pool generated with the bounded `Plus/Times/Minus/Div` grammar. The target family was not part of the earlier triangular/square/Euler transfer panel. Still, this is one small, authored scalar task with a deliberately informative finite candidate grid and three repetitions. It does not establish natural-task generalization, robustness to poor candidate grids, broad scaling, or autonomous induction. The prior off-grid false-singleton counterexample remains applicable: successful recovery here says nothing about whether a finite candidate pool contains or identifies the right model in a new task.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_CONTRACT_QUERY_GENERATED_CUBIC_TRANSFER_V1_PREREG_20261002.md)
- Runner: [source-locked runner](../../../evaluation/substrate_capability/substrate_contract_query_generated_cubic_transfer_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_generated_cubic_transfer_v1.py)
- Lock: [source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_generated_cubic_transfer_v1_lock_20261002.json)
- Capture: [raw worker data](../../../evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_analysis_20261002.json)
