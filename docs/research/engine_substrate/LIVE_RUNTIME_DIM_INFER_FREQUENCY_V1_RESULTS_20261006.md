# Live-runtime DimInfer frequency pilot v1 results

**Result: the six-execution extraction is source-locked and repeatable.** The
underlying capture and independent v1.6 analysis both pass their integrity
gates. Across three audit-on replicates, the two prompt routes produce:

| Prompt route | `DimInfer` argument calls | `term_eval:DimInfer` | `term_eval:ShapeDecode` | `term_unit:ShapeDecode` | `GenInfer` evals |
|---|---:|---:|---:|---:|---:|
| `report your organisation` | 1 each run | 2 each run | 3 each run | 17,392 each run | 0 each run |
| `describe who you are` | 0 each run | 0 each run | 0 each run | 0 each run | 0 each run |

Thus shape/dimension inference is present in one of these two fixed live
routes, while generic `GenInfer` is not observed in either. This does not
estimate prevalence over natural tasks: there are only two repeated
self-report prompt routes, not six independent tasks. Counts are instrumented
operation counters, not elapsed-time evidence; no cost ratio between different
counter units is inferred.

The capture is a deterministic re-analysis of the existing source-locked live
runtime data; it does not rerun the live system. The next prevalence gate
needs a task-diverse route panel and per-request counters before any claim that
induction is rare or frequent. See [protocol](LIVE_RUNTIME_DIM_INFER_FREQUENCY_V1_PREREG_20261006.md),
[runner](../../../evaluation/substrate_capability/live_runtime_dim_infer_frequency_v1.py),
[lock](../../../evaluation/substrate_capability/live_runtime_dim_infer_frequency_v1_lock_20261006.json),
[compact capture](../../../evaluation/reports/live_runtime_dim_infer_frequency_v1_20261006.json),
and [source live capture](../../../evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz).
