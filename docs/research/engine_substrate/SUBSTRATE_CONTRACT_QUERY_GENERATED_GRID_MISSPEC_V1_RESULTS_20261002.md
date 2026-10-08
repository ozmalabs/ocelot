# Generated-pool grid sensitivity and target misspecification v1 — results

## Result

Nine source/native-locked workers completed: three repetitions for each of deep cubic with a broad candidate grid, deep cubic with one candidate, and absolute value under an arithmetic-only grammar. The independent analyzer passes with zero errors, including current lock recomputation, worker hashes, pool integrity, independent query replay, paired arm parity, and label recomputation.

| Panel | Pool H | Median generation | Query result | Uncached → lazy native calls | Selector median, uncached → lazy | Held-out result |
|---|---:|---:|---|---:|---:|---|
| Cubic, size 7, broad grid | 66 | 669.91 ms | `x=12`; correct cubic survivor | 1,188 → 990 (−16.7%) | 6.470 → 6.686 ms | Exact in all three workers |
| Cubic, size 7, one-point grid | 27 | 141.15 ms | `x=2`; correct cubic survivor | 162 → 81 (−50%) | 0.832 → 0.691 ms | Exact in all three workers |
| Absolute value, arithmetic-only grammar | 9 | 401.86 ms | `x=−4`; zero survivors | 117 → 81 (−30.8%) | 0.646 → 0.638 ms | No exact target model; selector empties the version space |

The two cubic grids yield different generated pools because the candidate descriptors define behavioral deduplication. Both selected a single query that isolated the correct cubic expression, and all four cubic held-outs were exact. For absolute value, no generated expression matched all four held-outs. The first selected label eliminated every candidate in all three repetitions; the selector returned an empty version space rather than a false singleton.

## Interpretation and limits

This is evidence that a bounded query selector can flag one arithmetic-grammar misspecification case when its first informative label contradicts the whole pool. It also shows that a sparse candidate aperture can still suffice when its sole point distinguishes the target in this task. Lazy evaluation cut native calls in all panels, but selector latency was tied or slightly worse on the broad and misspecified tasks; synthesis dominated wall time. These results do not estimate misspecification detection rates, validate finite-grid adequacy in general, or imply robustness on natural tasks. The false-singleton risk remains whenever a wrong hypothesis agrees on all offered probes.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_CONTRACT_QUERY_GENERATED_GRID_MISSPEC_V1_PREREG_20261002.md)
- Runner: [source-locked runner](../../../evaluation/substrate_capability/substrate_contract_query_generated_grid_misspec_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_generated_grid_misspec_v1.py)
- Lock: [source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_generated_grid_misspec_v1_lock_20261002.json)
- Capture: [raw worker data](../../../evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_analysis_20261002.json)
