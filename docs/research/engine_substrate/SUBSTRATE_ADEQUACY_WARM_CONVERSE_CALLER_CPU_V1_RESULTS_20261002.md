# Warm converse caller-thread CPU diagnostic v1 — results

**Outcome: 8/8 gates pass.** Six fresh source-locked workers completed with exact held-out predictions, no codebook growth, unique PIDs, and a caller/other-thread CPU split reconciling to aggregate process CPU within 10 ms in every worker. The independent analyzer and source lock are retained with the [raw capture](../../../evaluation/reports/substrate_adequacy_warm_converse_caller_cpu_v1_raw_20261002.json).

| Setting | Rayon pool | Target wall median | Process CPU median | Caller-thread CPU median | Other-thread CPU median | Other-thread CPU share |
|---|---:|---:|---:|---:|---:|---:|
| Default | 24 | 111.3 ms | 1,646.0 ms | 85.4 ms | 1,560.5 ms | 94.8% |
| `RAYON_NUM_THREADS=1` | 1 | 111.7 ms | 1,642.5 ms | 86.3 ms | 1,559.8 ms | 94.8% |

The single-thread Rayon cap is confirmed to take effect, yet it does not reduce aggregate process CPU or target wall time. The caller-thread timing is only about 85–86 ms; roughly 1.5–1.6 seconds of CPU accrues on other process threads in both arms. Combined with the companion [pool diagnostic](SUBSTRATE_ADEQUACY_WARM_CONVERSE_RAYON_POOL_V1_RESULTS_20261002.md), which measures a 23-thread process increase during the target call in both settings, this establishes that the CPU/wall gap is real concurrent work outside the caller and outside the capped Rayon pool. It does not identify which library, native service, scheduler, or rule work consumed that CPU.

## Interpretation and next step

This changes the next measurement from “is `process_time` a misleading aggregate?” to “which concurrent workers are active and what work do they perform?” Source review found an independent cognitive-task execution path: `resolve_worker_capacity(None)` uses `available_parallelism`, and `execute_prepared` spawns scoped workers. The live conversation route has not yet been shown to invoke that path, so it remains a candidate, not an attribution. Next record task-run summaries and rule/matcher work around the target route, collect per-thread CPU deltas, and determine whether the extra 23 threads are task workers or another runtime pool.

The read-only `rayon_current_num_threads()` diagnostic is exposed by [the native binding](../../../runners/dsl/src/py.rs) and [Python wrapper](../../../runners/dsl/python/substrate_rs/__init__.py). The [protocol](SUBSTRATE_ADEQUACY_WARM_CONVERSE_CALLER_CPU_V1_PREREG_20261002.md), [runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_caller_cpu_v1.py), and source lock make the measurement reproducible. One host and three repeats per arm are diagnostic, not a population estimate.
