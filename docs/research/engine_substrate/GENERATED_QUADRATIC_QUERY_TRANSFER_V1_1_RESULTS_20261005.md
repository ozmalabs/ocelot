# Generated quadratic query-transfer v1.1 results

## Result

The source/native-locked capture passes all eight admission checks across 120 policy runs. On each scalar component of the coupled quadratic map, the size-5 `Plus, Times` generator explores 58 candidates and returns a two-term version space. One term is exact on all six held-out points; the other is a shortcut consistent with all six training labels. Both pools halt at the registered `max_size` boundary.

Maximum-entropy selection identifies the exact held-out behavior after one oracle call in all 20 grid permutations for each task. Fixed-first uses a mean 1.2 calls for the first output and 1.3 for the second; seeded random uses 1.1 and 1.2. Median calls are one for all policies. The selector evaluates a median of 72 hypothesis/input pairs per decision and takes 0.362 ms and 0.321 ms median per task; fixed-first and random each evaluate two hypotheses per decision and take 0.011 ms and 0.010 ms. Pool generation takes 9.2 ms and 12.1 ms for the two tasks. Thus this integration works and avoids some labels on the randomized finite grid, but its compute cost exceeds the saved oracle calls in this cheap synthetic-oracle setting.

## Interpretation and limits

This is direct evidence that existing bounded synthesis can produce a useful version space, and the existing disagreement selector can use a queried label to eliminate an overfitting candidate while retaining an exact held-out program. It does not show that the substrate discovers when to synthesize, chooses its grammar or query domain, validates oracle reliability, or changes its own implementation. The task set has two related scalar functions, a fixed grammar, a finite hand-authored input grid, and a simulated exact oracle. Twenty permutations per task measure order sensitivity, not independent task prevalence. Query selection is Python orchestration over candidate Terms evaluated by the native engine; hypotheses and their version-space state are not made graph-resident by this experiment.

## Reproduction

The [protocol](GENERATED_QUADRATIC_QUERY_TRANSFER_V1_PREREG_20261005.md) specifies the design. V1's failed independent replay is preserved; [v1.1 amendment](GENERATED_QUADRATIC_QUERY_TRANSFER_V1_1_AMENDMENT_20261005.md) records its correction. The source lock is [here](../../../evaluation/substrate_capability/generated_quadratic_query_transfer_v1_1_20261005_lock.json); [runner](../../../scripts/substrate_generated_quadratic_query_transfer_v1_1.py), [analyzer](../../../scripts/analyze_generated_quadratic_query_transfer_v1_1.py), [raw capture](../../../evaluation/reports/generated_quadratic_query_transfer_v1_1_20261005_raw.json), and [analysis](../../../evaluation/reports/generated_quadratic_query_transfer_v1_1_20261005_analysis.json) preserve the complete evidence.
