# GenInfer full-rank sorted identity-join scale v2.3 results

All preregistered gates pass across 144 fresh workers at N=128/512/2,048. Source and target training rows are independently and deterministically shuffled; both binaries receive the same two permutations for each paired case. The corrected order-independent oracle check passes for positives and controls. Exact train/held-out semantic parity, positive matrix acquisition and reuse, all refusal controls, source/binary provenance, native counter conservation, valid paired permutations, and the comparison-work gate pass.

Median audit-on train key-field comparisons across three positive matrix families × two repetitions:

| Relations | Nested | Sorted | Reduction |
|---:|---:|---:|---:|
| 128 | 65,536 | 5,896 | 11.1× |
| 512 | 1,048,576 | 28,172 | 37.2× |
| 2,048 | 16,777,216 | 129,600 | 129.5× |

Nested comparisons remain exactly `4N²`. Shuffled ordering increases sorted comparisons relative to the ascending-order v2.1 capture (for N=2,048: 40,944 → 129,600), but the candidate still uses about 129× fewer key-field comparisons than the nested scan. This is direct measured evidence for reduction under these independent permutations. The sorted implementation retains O(N log N) worst-case sort plus O(N) merge; this panel is not a general ordering distribution or proof about natural workload frequency.

The v2.2 capture is retained as a failed analysis artifact: both native arms acquired the expected matrices, but the runner's independent oracle flag compared deliberately shuffled relation lists positionally. V2.3 fixes that oracle by canonicalizing relation rows before comparison. See [v2.2 capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_2_20261006.json) and [preserved failed analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_2_analysis_initial_failure_20261006.json). V2.3 reproduction: [protocol](GENINFER_FULL_RANK_SORTED_JOIN_SCALE_V2_3_PREREG_20261006.md), [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2_3.py), [frozen analyzer](../../../evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v2_3.py), [capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_3_20261006.json), and [analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_3_analysis_20261006.json).

The “nonlinear” control is the within-frame map `z := z + x*y`. It probes the linear matrix solver's refusal boundary, not `TimeInfer` order-N extrapolation. The latter predicts nonlinear-in-time trajectories by finite differences over rigid-translation offsets and has separate order-2/order-3 evidence in [Generic Order-N results](GENERIC_ORDER_N_RESULTS.md). Arbitrary within-frame nonlinear map induction remains distinct and unproven.
