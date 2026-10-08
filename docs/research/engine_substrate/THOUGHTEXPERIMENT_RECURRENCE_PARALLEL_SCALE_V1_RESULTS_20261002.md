# Thoughtexperiment recurrence parallel scale v1 results

All six fresh workers pass the locked gates at 1,000,000 linked noise nodes. Each sequential and concurrent wave evaluates eight isolated branches over the same 64 recurrence candidates: every branch restores the authored guard, emits one offer per candidate, reaches fixed point, and preserves primary graph/rules/revision. Sequential and concurrent outcomes match, as do full-copy and shared-page semantics.

## Throughput and memory at fanout eight

Medians across three workers per backend/mode:

| Backend | Mode | Wave time | Experiments/s | Peak ΔPSS |
|---|---|---:|---:|---:|
| Full copy | Sequential | 4,220 ms | 1.90 | 360 MiB |
| Full copy | Concurrent | 10,659 ms | 0.75 | 2,053 MiB |
| Shared graph pages | Sequential | 746 ms | 10.73 | 142 MiB |
| Shared graph pages | Concurrent | 517 ms | 15.47 | 1,129 MiB |

The shared-page concurrent wave is 1.44× its sequential throughput; full-copy concurrency is 0.40× sequential throughput. Relative to the 100k recurrence wave, the shared-page concurrent gain falls from 1.78× to 1.44×, and full-copy concurrent performance changes from 0.85× to 0.40×. Concurrent fanout raises peak PSS substantially: about 8.0× shared-page sequential PSS and 5.7× full-copy sequential PSS at this scale. Thus concurrent exploration can raise throughput for the shared-page backend on this workload, while consuming substantially more resident memory; the full-copy arm becomes slower as well as larger.

Python-level branch creation remains serialized at the GIL boundary; native rule closure can overlap. The measured outcome is therefore concurrent rehearsal with serialized fork setup, not end-to-end parallel branch creation. `smaps_rollup` is sampled every 10 ms and can miss shorter peaks. The host reports and workload, the one recurrence family, and the synthetic linked noise graph bound these results; no natural-task, cross-host, open-ended-discovery, or asymptotic claim follows.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_SCALE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_parallel_scale_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_parallel_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_scale_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_parallel_scale_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_parallel_scale_v1_analysis_20261002.json)
