# GenInfer full-rank sorted identity-join scale v2.1 results

The corrected, preregistered analyzer passes all gates on 240 fresh workers spanning N=8/32/128/512/2,048; three positive 3-D matrices; rank-deficient, nonlinear, and duplicate-ID controls; two repetitions; two alignment builds; and scale audit on/off. Runner, analyzer, and protocol hashes match the capture, the two binary hashes are stable and distinct, Rust source manifests match across arms and stay stable in every worker, semantic outcomes match exactly, all positives transfer their acquired generator to held-out data, all negative controls refuse, and both native work-accounting invariants pass.

The direct audit counter counts each typed identity-key field comparison. Median train counts over the three positive geometries and two repetitions are:

| Relations | Nested comparisons | Sorted comparisons | Nested / sorted |
|---:|---:|---:|---:|
| 8 | 256 | 144 | 1.8× |
| 32 | 4,096 | 624 | 6.6× |
| 128 | 65,536 | 2,544 | 25.8× |
| 512 | 1,048,576 | 10,224 | 102.6× |
| 2,048 | 16,777,216 | 40,944 | 409.8× |

Nested counts are exactly `4N²` on these positive workers because the closure makes four full-rank alignment calls and each scans every source/target pair. Sorted counts include comparisons during sort, duplicate detection, and merge. Held-out alignment counts are zero: the just-minted graph-resident generator is reused, so the held-out phase does not rerun matrix acquisition.

This establishes a large reduction in measured key-comparison work for these cases. The registered IDs are inserted and supplied in ascending order, and the runtime sort sees already/nearly sorted keys. That order is favorable to the sort implementation; it does not measure shuffled or adversarial key order. Source complexity remains O(N²) for nested probes and O(N log N) worst case for sorting plus O(N) merging, but a randomized-order capture is needed before generalizing the measured comparison-count curve.

Audit-off timing from the work-audit-enabled binaries is diagnostic, not a clean speed claim: at N=2,048 median train closure is 245.3 ms nested vs 175.7 ms sorted (paired change −28.1%), while small sizes vary around parity. The counter instrumentation still adds a branch per key-field comparison even with audit disabled. The earlier uninstrumented v1 found no clear crossover through N=128. Rerun clean timing binaries at larger sizes before promoting an end-to-end acceleration. Process max-RSS includes Python and substrate startup and is not a join-allocation measure.

The “nonlinear” control in this workload remains the within-frame warp `z := z + x*y`; it validates refusal by this linear matrix inducer, not `TimeInfer` order-N extrapolation. The latter's polynomial trajectory capability has separate measured order-2/order-3 evidence in [Generic Order-N results](GENERIC_ORDER_N_RESULTS.md). Neither result supports arbitrary nonlinear map induction.

The first v2 capture and analyzer failure are preserved at [v2 capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_20261006.json) and [initial failed analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_analysis_initial_failure_20261006.json). The failure was an analyzer expression that included the new comparison counter in attempt conservation; v2.1 freezes the corrected sum and repeats the full cohort. Reproduction: [v2.1 protocol](GENINFER_FULL_RANK_SORTED_JOIN_SCALE_V2_1_PREREG_20261006.md), [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2_1.py), [frozen analyzer](../../../evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v2_1.py), [capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_1_20261006.json), and [analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_1_analysis_20261006.json).
