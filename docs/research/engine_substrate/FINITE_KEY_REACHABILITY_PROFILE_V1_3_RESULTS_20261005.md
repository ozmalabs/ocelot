# Finite-key reachability profile v1.3 results

## Result

All 60 locked cases passed nine independent checks: binary and ternary N=128 trees, 30 fresh-substrate repetitions each, exact DFS/materialized-relation parity, exact direct and materialized answers at Q=32,64,128,256, bounded fixed points, lock stability, alternating measurement order, and refusal of the unrestricted fresh-node control.

The preregistered robust-crossover rule (median paired ratio below one and at least 24/30 repetitions favoring materialization) is met in no cell. At Q=256, binary-tree median direct total is 184.348 ms and profile total is 175.990 ms; median paired ratio is 0.941, with 23/30 repetitions favoring materialization. Ternary-tree medians are 174.837 ms direct and 170.350 ms profile; paired ratio 0.955, with 20/30 favorable. Binary Q=128 has a 0.964 median paired ratio (21/30 favorable). The Q=32 medians remain just above parity, and Q=64 results are near parity.

A separately reproducible **post-hoc** paired bootstrap (50,000 resamples of the 30 within-cell paired ratios; percentile interval for the median) places the 95% interval below one for binary Q=128 [0.915, 0.992], binary Q=256 [0.912, 0.968], and ternary Q=256 [0.924, 0.998]. Other intervals include one. These exploratory intervals were not part of the preregistered decision rule and should not be treated as confirmatory evidence.

## Interpretation

On these two N=128 synthetic tree shapes, sufficiently repeated all-source queries appear capable of making a materialized relation modestly cheaper end to end. The effect is small (about 2.5–6% by median paired ratio in the strongest Q cells), does not meet the preregistered 24/30 consistency threshold, and is not established for natural workloads. The v1.1 N=64/Q=8 crossover still failed replication. This resolves only the narrow economics of this relation on these tree generators; it does not support a general substrate speedup or natural-task frequency claim.

The next useful gate is to test whether naturally authored substrate tasks contain repeated query workloads that can reuse a derived relation, including the cost of recognizing/maintaining that relation as input changes. Otherwise, further synthetic query-count extension has diminishing value.

## Reproduction and evidence

Run the source-locked [v1.3 protocol](FINITE_KEY_REACHABILITY_PROFILE_V1_3_PREREG_20261005.md), runner `evaluation/substrate_capability/finite_key_reachability_profile_v1_3.py`, then analyzer `evaluation/substrate_capability/analyze_finite_key_reachability_profile_v1_3.py`. The capture and primary analysis are [raw data](../../../evaluation/reports/finite_key_reachability_profile_v1_3_20261005.json) and [analysis](../../../evaluation/reports/finite_key_reachability_profile_v1_3_analysis_20261005.json). The exploratory bootstrap is reproducible with `evaluation/substrate_capability/posthoc_finite_key_reachability_v1_3_uncertainty.py`; its output is [here](../../../evaluation/reports/finite_key_reachability_profile_v1_3_uncertainty_posthoc_20261005.json).
