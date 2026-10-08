# ShapeDecode name-aperture cache v1 — results

## Result

The source-locked 80-worker panel passed all 12 preregistered checks. It compared the existing scan route with an EvalCtx-local parsed-codebook cache, using five fresh processes per cell, four effective codebook populations, and traced and untraced arms. Every worker selected the exact target; paired arms had identical outputs and coarse closure work, traced and untraced outcomes agreed, traces were complete, the scan arm reproduced the earlier baseline work counts, and each cache arm recorded hits and misses.

| Effective parts (P) | Population visits, scan → cache | Reduction | Median untraced closure, scan → cache | Median wall speedup |
|---:|---:|---:|---:|---:|
| 33 | 2,178 → 66 | 96.97% | 15.72 → 3.64 ms | 4.32× |
| 49 | 4,802 → 98 | 97.96% | 23.76 → 4.33 ms | 5.48× |
| 81 | 13,122 → 162 | 98.77% | 42.09 → 6.18 ms | 6.81× |
| 145 | 42,050 → 290 | 99.31% | 87.38 → 10.03 ms | 8.71× |

The cached counts equal one full parse per candidate (two passes) plus aperture-selected candidate parts. Cache hit medians rise from 64 to 288 across the panel; each worker records two misses. CPU and wall speedups track closely. Median peak RSS ranges from 53.5–53.9 MiB in cached workers and 53.5–54.3 MiB in scan workers, with no clear RSS difference at this resolution.

## Interpretation and limits

This is evidence that repeated population scans dominate this one candidate-at-a-time, name-scoped ShapeDecode route, and that parsed-codebook reuse can remove most of that work while improving end-to-end closure time at populations up to 145 effective parts. It is a measured local optimization, not a general tractability result or a natural-task prevalence estimate. The timing workload uses an authored cross-frame identity fixture and lower-case unique names. The companion [semantic panel](SHAPEDECODE_NAME_APERTURE_SEMANTICS_V1_RESULTS_20261005.md) separately tests case variation, exact and case-fold-equivalent duplicates, missing and empty scopes, and reversed requested-name order. Neither panel covers `Surface(Text)` attributes, malformed out-of-scope entries, exclusion filters, mutation lifecycle, large production codebooks, or naturally occurring name distributions. Those remain open before broad promotion.

The cache is scoped to an immutable EvalCtx and is used only when a name scope is declared; the legacy scan path remains available through the runtime switch. The implementation performs the original full loader on a miss, preserving validation behavior for unrelated malformed records, then uses insertion-order name positions for repeated selections. The runtime and semantic panels validate selected authored routes only. No inference is made about the cheap-cut hypothesis, frame separators, Rung 3/4 induction, or general capability.

**Post-hoc trace overhead screen:** the existing capture contains five matched traced/untraced process pairs for each cache mode and population. All 40 pairs match closure work and semantic readback; all 80 workers have distinct PIDs, stable source manifests, and complete traces. Median traced/untraced wall ratios range from 1.008–1.029 in scan mode and 0.977–1.038 in cached mode. Individual ratios span 0.851–1.194 for scan and 0.775–1.116 for cached, so host and scheduler variation is large relative to the observed differences. This post-hoc five-pair screen does not estimate a stable instrumentation tax or correct the cache speedup; a preregistered larger overhead panel remains open. See the [post-hoc analyzer](../../../evaluation/substrate_capability/analyze_shapedecode_trace_overhead_posthoc_v1.py) and [paired analysis report](../../../evaluation/reports/shapedecode_trace_overhead_posthoc_v1_20261005.json).

**Live-route applicability check:** the source audit of the active `shape_decode_loop` seed finds three global ShapeDecode Terms and zero name-scoped ShapeDecode Terms. The selected live-helper capture records three runtime ShapeDecode calls on this ladder route, each scanning the shared codebook; `eval_shape_decode` only enters the cache branch when `scope_idx.is_some()`. Thus these cache speedups do not apply to the measured default ladder route as currently authored. The codebook-scope semantic and timing panels measure capability when a name aperture is present, not the prevalence of such apertures in normal operation. See the [seed scope audit](../../../evaluation/reports/shape_decode_seed_scope_audit_v1_20261005.json), [live helper work analysis](../../../evaluation/reports/live_helper_work_capture_v1_4_analysis_20261005.json), and [cache gate implementation](../../../runners/dsl/src/shape_decode.rs).

## Artifacts

- [Preregistration and amendment](SHAPEDECODE_NAME_APERTURE_CACHE_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/shapedecode_name_aperture_cache_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_shapedecode_name_aperture_cache_v1.py)
- [Raw capture](../../../evaluation/reports/shapedecode_name_aperture_cache_v1_20261005.json)
- [Analysis](../../../evaluation/reports/shapedecode_name_aperture_cache_v1_analysis_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/shapedecode_name_aperture_cache_v1_lock_20261005.json)
