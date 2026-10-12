# GenInfer full-rank sorted identity-join scale v1 results

The preregistered 144-worker capture passes every gate. It covers N=8/32/128, three distinct full-rank 3-D matrices, rank-deficient, nonlinear, and duplicate-ID controls, two fresh workers per family and size, both audit states, and both alignment binaries. The captured runner, analyzer, and protocol hashes match their frozen source files; each binary hash is stable and distinct; Rust source manifests match; source stays stable inside workers; and native counters conserve in every audited phase.

The nested and sorted arms have exact agreement for every paired train and held-out outcome: status, coverage, residual, transform receipts, closure work, and generator library. Both arms acquire each positive matrix, recognize and transfer it to held-out observations, and reject all three negative controls without minting. This establishes semantic parity on these authored 3-D identity fixtures.

The nonlinear control is a static within-frame warp (`z := z + x*y`), selected to challenge the integer-linear matrix solver. It does not test temporal order-N extrapolation. The separate [`TimeInfer` order-N path](GENERIC_ORDER_N_RESULTS.md) extrapolates sequences of rigid-translation offsets and has measured order-2 and order-3 cases. These capabilities should be assessed separately from learning arbitrary nonlinear maps within a frame.

## Audit-off positive timing

Medians aggregate the three positive geometries × two repetitions at each relation count. The paired percentage is the median of per-case `sorted / nested − 1`; negative means sorted was faster. Times are closure wall time in milliseconds.

| Relations | Train nested | Train sorted | Paired train change | Held-out nested | Held-out sorted | Paired held-out change | Median RSS nested → sorted |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 1.571 | 1.542 | −3.4% | 0.851 | 0.830 | −0.7% | 48,098 → 48,352 KiB |
| 32 | 2.471 | 2.537 | +3.7% | 1.584 | 1.636 | −3.3% | 47,914 → 48,198 KiB |
| 128 | 6.849 | 6.679 | −0.7% | 4.603 | 4.349 | −2.3% | 48,214 → 48,238 KiB |

At these sizes, full closure timing is effectively at parity: direction varies with size and phase, and the candidate does not establish a stable speedup. Median process maximum RSS differs by 24–284 KiB; this includes the Python worker and substrate startup and does not isolate join allocation. The candidate's source structure is O(N log N) key sorting plus O(N) merge, versus O(N²) target probes in the nested alignment, but this capture has no direct comparator counter. The asymptotic work change is therefore source-derived; its practical crossover remains unmeasured.

Keep the candidate opt-in and do not cite this as an end-to-end acceleration. The next gate should add direct identity-key comparison counters and extend the same paired workload to larger safe N (for example 512/2,048/8,192), while recording peak memory attributable to alignment if an isolated measure can be obtained. Preserve exact semantic and refusal controls. Even a confirmed join crossover would address one solver kernel only; it would not establish natural frame locality, natural-task prevalence, rung 3–4 tractability, or general capability.

Reproduction: [protocol](GENINFER_FULL_RANK_SORTED_JOIN_SCALE_V1_PREREG_20261006.md), [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v1.py), [frozen analyzer](../../../evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v1.py), [capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v1_20261006.json), and [analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_scale_v1_analysis_20261006.json).
