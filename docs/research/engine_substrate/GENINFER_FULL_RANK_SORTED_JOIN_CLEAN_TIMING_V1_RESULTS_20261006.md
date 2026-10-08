# GenInfer full-rank sorted identity-join clean timing v1 results

All 72 preregistered clean workers pass. The binaries omit comparison-counter instrumentation; source and target rows are independently shuffled; binary/source provenance and independent matrix oracles pass; paired semantic fields match exactly; both arms acquire and reuse all three positive matrices; and rank-deficient, nonlinear within-frame, and duplicate-ID controls refuse without minting.

Each size has six paired positive cases (three matrix geometries × two fresh repetitions). The paired percentage is the median per-case `sorted / nested − 1`; negative means sorted was faster. Closure wall medians are milliseconds:

| Relations | Train nested | Train sorted | Paired train change | Held-out nested | Held-out sorted | Paired held-out change | Median RSS nested → sorted |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 7.531 | 7.160 | −9.7% | 4.857 | 4.484 | −4.2% | 48,548 → 48,618 KiB |
| 512 | 31.248 | 27.317 | −13.6% | 16.658 | 16.028 | −3.6% | 49,286 → 49,688 KiB |
| 2,048 | 263.132 | 187.261 | −29.8% | 62.297 | 62.925 | −0.5% | 54,642 → 55,202 KiB |

This uninstrumented capture shows a repeatable train-closure reduction on the shuffled authored workloads: all six N=2,048 positive pairs favor the sorted arm by 26.4–36.2%, and all six N=512 pairs favor it by 10.7–21.8%. At N=128 five of six pairs favor sorted. The held-out phase is nearly unchanged at larger N, consistent with its reuse path bypassing matrix alignment. Process high-water RSS includes Python and substrate startup, so its 70–560 KiB difference does not isolate join allocation.

Median process CPU time closely tracks wall time. Train CPU nested→sorted is 7.520→7.159 ms at N=128, 31.234→27.310 ms at N=512, and 262.931→186.698 ms at N=2,048. Held-out CPU is 4.858→4.482 ms, 16.660→16.026 ms, and 62.291→62.929 ms at those sizes, respectively.

This supports the sorted join as a useful optimization for large identity-aligned 3-D frames. It does not support enabling the solver or join by default: acquisition remains a narrow, authored capability; the benchmark covers only 1-D/3-D solver paths in the broader series; and natural-task prevalence, broader key distributions, higher-dimensional maps, and whole-substrate scaling remain open. Next measure production-derived relation/key distributions and compare with the current engine's ordinary GenInfer traffic before setting defaults.

Reproduction: [protocol](GENINFER_FULL_RANK_SORTED_JOIN_CLEAN_TIMING_V1_PREREG_20261006.md), [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_clean_timing_v1.py), [frozen analyzer](../../../evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_clean_timing_v1.py), [capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_clean_timing_v1_20261006.json), and [analysis](../../../evaluation/reports/geninfer_full_rank_sorted_join_clean_timing_v1_analysis_20261006.json).
