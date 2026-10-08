# FSDD matcher selection v1.3 analysis amendment

The locked v1.2 analyzer used `0` as the fallback selected-system accuracy when a fold had no selected proposal. This made the abstained fold's descriptive regret appear numerically equal to its hindsight-best accuracy, although regret is undefined without a selected system. The post-capture v1.3 analyzer records both selected accuracy and regret as null for that fold. It leaves the preregistered gates unchanged: the unique-selection, above-chance-selection, and regret gates fail because the fold abstained. The lock, training orders, held-out scores, source hashes, and substrate behavior are unchanged. The v1.2 analysis artifact is preserved.

Corrected analysis: [v1.3 analysis JSON](../../../evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_3_analysis_20261002.json); analyzer: [v1.3 analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_fsdd_matcher_selection_v1_3.py).
