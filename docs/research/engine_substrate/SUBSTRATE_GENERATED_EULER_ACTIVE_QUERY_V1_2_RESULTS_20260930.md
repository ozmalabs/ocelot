# Generated Euler Active Query v1.2 Results

**Superseded for final use:** a subsequent synthetic branch replay found that the initial cached filter used exact numeric equality while the uncached CEGIS path used a `1e-9` tolerance. The v1.2 capture is preserved as historical evidence; use the corrected [v1.2.1 results](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_2_1_RESULTS_20260930.md) and the branch-reuse measurement for final cache conclusions.

**Result:** the cached ranking index exactly reproduced the uncached entropy query sequence in all three anchors and reduced repeated decision work, but its one-time matrix build cost erased that gain for one episode. The cache became cost-favorable in a two-episode amortization calculation; that multi-episode reuse case still needs direct measurement.

| Policy | Median oracle calls | Median decision work | Median query-oracle work | Median total incl. one-time cache build |
|---|---:|---:|---:|---:|
| Entropy, uncached | 3 | 32.29 ms | 0.225 ms | 32.46 ms |
| Entropy, cached | 3 | 4.76 ms | 0.207 ms | 34.05 ms |
| Fixed first | 7 | 4.03 ms | 0.384 ms | 4.33 ms |
| Seeded random | 4 | 2.70 ms | 0.236 ms | 3.02 ms |

Cached and uncached entropy made the same query sequences for every anchor. The matrix evaluated each generated-hypothesis/candidate pair once: 7,944 pairs for the 662-hypothesis pool, 5,352 for 446, and 2,616 for 218. Median cache construction was 29.0 ms, and the retained Python heap estimate was 642,367 bytes. The heap estimate counts Python values and comparison keys; it excludes native term objects, allocator overhead, and process-level RSS. After construction, cached entropy's median per-episode decision-plus-oracle time was 4.92 ms, compared with 32.46 ms uncached. Charging the 29.0 ms build once, the simple median-cost model crosses over at two episodes reusing the same pool and candidate set (`29.0 + 2×4.92 < 2×32.46`). This is an arithmetic projection from single-episode measurements, not a measured multi-branch result.

All policies retained the six-holdout-correct behavior and identified it uniquely on every run. This repeats the earlier bounded Euler result; it does not establish broader tractability. The cache is immutable and tied to a particular hypothesis pool, descriptors, and candidate set. Next measure actual multi-branch reuse and memory residency, then extend to a task where fixed-first or random has a materially lower success rate.

## Evidence

- [Original preregistration](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_PREREG_20260930.md)
- [v1.1 cost amendment](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_1_AMENDMENT_20260930.md)
- [v1.2 cache amendment](SUBSTRATE_GENERATED_EULER_ACTIVE_QUERY_V1_2_AMENDMENT_20260930.md)
- [Source-locked v1.2 runner](../../../scripts/substrate_generated_euler_active_query_v1_2.py)
- [Analyzer](../../../scripts/analyze_substrate_generated_euler_active_query_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_generated_euler_active_query_v1_2_20260930_lock.json)
- [Raw capture](../../../evaluation/reports/substrate_generated_euler_active_query_v1_2_20260930_raw.json)
- [Analysis capture](../../../evaluation/reports/substrate_generated_euler_active_query_v1_2_20260930_analysis.json): 431 checks passed, zero failed.
