# Shape-decoding concurrency phase profile v1 — results

**Result:** 7/7 gates pass across 12 fresh processes. Each wave runs eight positive shape-axis rehearsals; sequential/concurrent and full-copy/shared-page outcomes match. Primary revision/counts/rules remain unchanged, and source/native locks match. The host allowed CPUs `0-23` (24 logical CPUs); cgroup CPU quota was unavailable.

| Backend | Mode | Wave wall ms | Sum thread CPU ms | CPU/wall | Snapshot/setup ms per branch | Candidate patch ms per branch | Model-after prediction ms per branch | Bounded forward look ms per branch |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `native_full_copy_scoped` | sequential | 1693.4 | 1653.6 | 0.98× | 36.4 | 17.5 | 153.3 | 138.4 |
| `native_full_copy_scoped` | concurrent | 2743.9 | 2685.6 | 0.98× | 423.3 | 145.5 | 1570.3 | 586.9 |
| `native_shared_graph_pages_scoped` | sequential | 721.6 | 713.4 | 0.99× | 8.9 | 18.4 | 60.3 | 45.1 |
| `native_shared_graph_pages_scoped` | concurrent | 1082.1 | 1072.7 | 0.99× | 116.1 | 134.6 | 637.1 | 131.4 |

Aggregate per-thread CPU stays close to wall time in both modes (0.98–0.99×), so this workload used about one CPU-second per wall-second despite eight worker threads. Threading did not produce measurable CPU overlap here. At the same time, per-branch wall phases expand substantially during concurrent waves: shared-page snapshot/setup rises from 8.9 ms sequential to 116.1 ms concurrent, and model-after prediction from 60.3 to 637.1 ms. Full-copy phases show a similar expansion. This indicates contention or serialization in the end-to-end path, but CPU/wall and phase wall times cannot identify whether the cause is GIL-held Python work, native shared locks, allocator/memory contention, or a combination.

The profile is exploratory (three fresh-process repeats per cell). `thread_time_ns` measures CPU consumed by each worker, not GIL ownership; phase timers include Python and native work, and nested phase values overlap. This result localizes the scaling symptom more sharply but is not a root-cause proof. Next collect a GIL-aware profile and native lock/allocator counters, or implement a same-oracle native batch entry point and compare it with the current Python orchestration.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_concurrency_profile_v1_raw_20261001.json)
- [Sequential phase profile](THOUGHTEXPERIMENT_SHAPE_DECODING_PHASE_PROFILE_V1_RESULTS_20261001.md)
- [End-to-end parallel wave](THOUGHTEXPERIMENT_SHAPE_DECODING_PARALLEL_WAVE_V1_RESULTS_20261001.md)
