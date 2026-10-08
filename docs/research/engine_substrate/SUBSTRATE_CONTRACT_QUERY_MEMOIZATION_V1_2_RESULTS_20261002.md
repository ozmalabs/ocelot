# Contract query memoization v1.2 — results

All 24 paired source-locked workers completed successfully. All four arms produced exactly the same query histories, Term predictions, oracle labels, and final singleton. The callback-backed `Holds` control executed four times and stored zero cache entries under the JSON, fingerprint, and identity cache routes, confirming that graph-dependent terms bypass this cache path.

| Workload | No cache | JSON cache | Fingerprint cache | Identity cache |
|---|---:|---:|---:|---:|
| H=128, N=28 | 187.38 ms | 496.25 ms | 323.05 ms | 297.19 ms |
| H=32, N=500 | 474.74 ms | 1,318.03 ms | 797.63 ms | 785.48 ms |
| H=512, N=36 | 1,317.03 ms | 3,310.31 ms | 2,015.54 ms | 1,999.54 ms |

Memoization reduced native evaluation calls by 1.96–2.59×, but the identity-keyed cache still ran 1.51–1.66× slower than no cache. The fingerprint cache ran 1.54–1.72× slower, and JSON-per-lookup ran 2.50–2.78× slower. At H=512, peak RSS was roughly 42–44 MB without a cache, 69 MB with JSON, and 42–46 MB for the object-reference caches. The faster identity lookup improves on the first JSON design, but cache bookkeeping, Python-level traversal, and value handling still outweigh the saved native calls in these workloads.

## Decision and limit

Do not enable memoization by default for this selector based on these results. The opt-in implementations remain available for controlled use with pure Terms, immutable input objects, and fixed evaluator context, but fewer native calls do not imply a faster search. The next performance experiment should change the search organization—such as evaluating a prediction matrix once and updating partitions incrementally, or a native batch scorer—then compare it against the uncached selector with the same exact semantic gates. Preserve the open-world false-singleton control: batching is not model-adequacy evidence.

This result is limited to integer-coded pure Terms, one host, and two repetitions per cell. It is not a verdict on caching expensive graph-dependent inference or other workloads where each evaluation is substantially more costly.

## Artifacts

- [Preregistration](SUBSTRATE_CONTRACT_QUERY_MEMOIZATION_V1_2_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_memoization_v1_2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_contract_query_memoization_v1_2.py)
- [Lock](../../../evaluation/substrate_capability/substrate_contract_query_memoization_v1_2_lock_20261002.json)
- [Capture](../../../evaluation/reports/substrate_contract_query_memoization_v1_2_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_memoization_v1_2_analysis_20261002.json)
