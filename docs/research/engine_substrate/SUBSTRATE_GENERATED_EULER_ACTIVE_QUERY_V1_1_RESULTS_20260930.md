# Generated Euler Active Query v1.1 Results

**Result:** entropy ranking reduced the oracle calls needed to isolate a hypothesis that matches all six independent held-out complexes, but its current repeated-ranking implementation cost substantially more local compute than fixed or random selection on this benchmark.

All three bounded hypothesis searches completed at `max_size`, explored 10,125–10,269 terms, and returned pools of 218–662 hypotheses. Each pool contained a hypothesis matching all six held-out labels. Across the point, edge, and triangle anchors, entropy uniquely identified a held-out-correct hypothesis in 3/3 runs using 2–3 oracle calls. Fixed-first did so in 3/3 using 5–7 calls. Seeded-random did so in 60/60 runs, with a median of 4 calls (range 2–9).

| Policy | Trials | Median oracle calls | Median internal prediction evaluations | Median decision compute | Median query-oracle time | Median decision + oracle time |
|---|---:|---:|---:|---:|---:|---:|
| Entropy ranked | 3 | 3 | 6,026 | 31.59 ms | 0.206 ms | 31.78 ms |
| Fixed first | 3 | 7 | 705 | 2.87 ms | 0.499 ms | 3.17 ms |
| Seeded random | 60 | 4 | 572 | 3.14 ms | 0.297 ms | 3.39 ms |

Generation took a median 0.961 seconds per anchor and is a common cost when the same generated pool is used by each policy. The current entropy selector recomputes predictions over the surviving pool and all remaining candidates on each round. Here, fewer oracle calls did not compensate for the extra local compute because the grounded oracle call itself took only about 0.1 ms per call. If oracle responses are expensive in a deployment, the economic tradeoff may differ; this benchmark does not measure external oracle latency.

This supports a narrow capability claim: the substrate can generate a bounded Euler hypothesis pool and iteratively choose informative queries that reduce labels needed on these synthetic structures. It does not show that the approach is cheaper end-to-end, generalizes to natural tasks, or solves open-ended hypothesis induction. The next engineering target is a cached prediction index or incremental entropy update, measured against this uncached baseline with the one-time matrix cost and memory included.

## Evidence

- [Original preregistration](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_PREREG_20260930.md)
- [Timing amendment](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_1_AMENDMENT_20260930.md)
- [v1.1 source-locked runner](../../../scripts/substrate_generated_euler_active_query_v1_1.py)
- [v1.1 analyzer](../../../scripts/analyze_substrate_generated_euler_active_query_v1_1.py)
- [v1.1 source lock](../../../evaluation/substrate_capability/substrate_generated_euler_active_query_v1_1_20260930_lock.json)
- [v1.1 raw capture](../../../evaluation/reports/substrate_generated_euler_active_query_v1_1_20260930_raw.json)
- [v1.1 analysis capture](../../../evaluation/reports/substrate_generated_euler_active_query_v1_1_20260930_analysis.json): 410 checks passed, zero failed.
- The original untimed [v1 capture](../../../evaluation/reports/substrate_generated_euler_active_query_v1_20260930_raw.json) is preserved separately; use v1.1 for cost comparisons.
