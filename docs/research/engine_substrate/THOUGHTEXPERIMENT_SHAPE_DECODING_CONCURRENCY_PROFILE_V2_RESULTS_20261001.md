# Shape-decoding concurrency profile v2 — GIL-release intervention results

**Result:** 7/7 gates pass across 12 fresh processes on the rebuilt native engine. All eight branches per run preserve the positive shape-axis correction oracle; sequential/concurrent and backend semantics match; primary state, source lock, and binary lock remain intact. The intervention moves `tick_graph_then_struct`’s unchanged native cycle inside `py.allow_threads`, while retaining the branch-local substrate mutex. See the [amendment](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V1_AMENDMENT_20261001.md) for why this binding change was selected.

| Backend | Mode | v1 CPU/wall | v2 CPU/wall | v1 wave ms | v2 wave ms | v2 snapshot/setup ms per branch | v2 patch ms per branch | v2 prediction ms per branch |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `native_full_copy_scoped` | sequential | 0.98× | 0.98× | 1693.4 | 1989.9 | 44.4 | 19.7 | 179.6 |
| `native_full_copy_scoped` | concurrent | 0.98× | 0.98× | 2743.9 | 3069.3 | 484.7 | 205.2 | 1573.3 |
| `native_shared_graph_pages_scoped` | sequential | 0.99× | 0.99× | 721.6 | 906.0 | 9.1 | 23.6 | 73.1 |
| `native_shared_graph_pages_scoped` | concurrent | 0.99× | 1.00× | 1082.1 | 1206.2 | 130.1 | 173.9 | 673.9 |

The intervention did not improve aggregate CPU overlap: it remains 0.98–1.00× in both modes. V2 concurrent median wave times are 3069 ms full-copy and 1206 ms shared-pages, compared with v1’s 2744 and 1082 ms. With three repeats and environmental variability, those time differences are not evidence of a regression; the relevant finding is no observed concurrency gain from releasing the cycle call alone. The largest remaining concurrent per-branch phases are model-after prediction and rule patching; shared-page snapshot/setup is also 130 ms under the wave versus 9 ms sequential. The high-level path still makes many Python-to-native graph/rule calls, whose bindings retain the GIL, and the full orchestration includes Python frontier traversal and readout. The targeted edit is therefore insufficient to unlock this pipeline.

The source change preserves the Python signature and task semantics. This does not prove the GIL is the sole bottleneck: allocator/memory contention and native locks remain plausible, and system `perf` counters are unavailable under `perf_event_paranoid=4`. Next measure Python/GIL-held work with an in-process profiler or move snapshot, candidate patch, prediction, and readout into a native batch operation behind the same semantic gates. Do not infer serving throughput from this one fixture.

## Artifacts

- [Original concurrency profile](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V1_RESULTS_20261001.md)
- [Intervention amendment](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V1_AMENDMENT_20261001.md)
- [V2 pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v2_lock_20261001.json)
- [V2 runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v2.py)
- [V2 raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_concurrency_profile_v2_raw_20261001.json)
- [Changed binding](../../../runners/dsl/src/py.rs)
