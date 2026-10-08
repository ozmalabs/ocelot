# Thoughtexperiment recurrence cancellation scale v1 results

All six fresh workers pass at 1,000,000 linked noise nodes. Each creates eight patched branches, drops four before rule closure, then runs the four survivors. Every surviving branch restores the authored recurrence guard, emits exactly one offer for all 64 candidates, reaches a zero-progress fixed point, and leaves the primary graph/rules/revision unchanged. Source and native provenance remain stable.

## PSS during branch cancellation and release

Medians across three workers per backend:

| Backend | Wall time | Sampled peak ΔPSS | Eight patched branches live | After dropping four | After survivor work and releasing all |
|---|---:|---:|---:|---:|---:|
| Full copy | 11,741 ms | 2,881 MiB | 2,881 MiB | 2,155 MiB | 1,683 MiB |
| Shared graph pages | 353 ms | 534 MiB | 72.0 MiB | 41.5 MiB | 10.5 MiB |

Dropping half the branches reduces sampled PSS by about 726 MiB full copy and 30.5 MiB shared pages. After all branch references are released, the shared-page process is about 10.5 MiB above its host baseline. Full-copy PSS remains about 1.65 GiB above baseline, despite branch references being cleared. The 10 ms sampled peak for shared pages (534 MiB) is much higher than its all-live checkpoint (72 MiB), showing a transient peak during concurrent setup or mutation; do not use the checkpoint alone as peak-memory evidence.
The follow-up [allocator attribution](THOUGHTEXPERIMENT_RECURRENCE_CANCEL_ALLOCATOR_V1_RESULTS_20261002.md) finds that the full-copy post-release PSS is largely free glibc arena residency: in-use bytes return close to baseline and `malloc_trim(0)` releases about 1.49 GiB of PSS.

The wall time covers concurrent branch creation/patch, dropping half, and closure/readout on the survivors. Shared pages complete about 33× faster than full copy in this fixture, but that is not a pure fork-speed ratio: the whole cancellation/closure wave is included. PSS after drop does not show whether remaining full-copy residency is live data or allocator retention. A matched glibc in-use/free-arena capture is the next attribution step for this multi-branch lifecycle. This is one authored recurrence family and one host; it does not measure cancellation during active native closure, general cancellation latency, natural-task success, or self-directed candidate search.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_CANCEL_SCALE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_cancel_scale_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_cancel_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_scale_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_analysis_20261002.json)
