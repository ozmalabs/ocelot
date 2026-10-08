# Active thoughtexperiment rehearsal memory v1 — results

**Result:** 5/5 amended confirmatory gates pass across the preregistered panel.

This panel samples current full-process RSS/PSS while the positive self-correction rehearsal actually predicts and reads out its residual. The graph fixture, loaded rules, candidate, and observations are retained. The primary may gain the normal durable correction trace; the gates verify that the noise graph, source observations, and rewrite rules remain unchanged. Timing is instrumented and descriptive because the 10 ms sampler perturbs scheduling.

| Added nodes | Backend | Baseline PSS | Peak PSS | Peak ΔPSS | Peak ΔPrivate Dirty | Runs converged |
|---:|---|---:|---:|---:|---:|---:|
| 100,000 | `native_full_copy_scoped` | 69.2 MiB | 167.6 MiB | 98.32 MiB | 97.26 MiB | 3/3 |
| 100,000 | `native_shared_graph_pages_scoped` | 69.2 MiB | 79.4 MiB | 10.17 MiB | 9.11 MiB | 3/3 |
| 200,000 | `native_full_copy_scoped` | 101.1 MiB | 291.8 MiB | 190.77 MiB | 189.71 MiB | 3/3 |
| 200,000 | `native_shared_graph_pages_scoped` | 100.1 MiB | 115.0 MiB | 14.93 MiB | 13.87 MiB | 3/3 |

Interpret these as one synthetic positive correction family on one Linux host. The active operation uses branch prediction and residual readout, but does not cover the negative correction arm, parallel candidate batches, kernel peak RSS, or unrelated graph families. The sampler may miss peaks shorter than its interval; no timing superiority is inferred. The initial attempt's extra primary-edge-count gate was invalid because the production path intentionally writes durable trace nodes/edges; its raw capture is retained as a [harness diagnostic](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_initial_diagnostic_raw_20261001.json). The amended gate checks task-input and rule preservation.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_PREREG_20261001.md)
- [Amendment](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_AMENDMENT_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_active_rehearsal_memory_v1.py)
- [Initial diagnostic](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_initial_diagnostic_raw_20261001.json)
- [Confirmatory raw capture](../../../evaluation/reports/thoughtexperiment_active_rehearsal_memory_v1_raw_20261001.json)
