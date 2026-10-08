# Thoughtexperiment recurrence allocator reclamation v1 results

All six fresh-process workers pass source, repair, and isolation gates at 1,000,000 linked noise nodes. Each backend restores the exact authored recurrence guard, emits one offer, reaches a zero-progress fixed point, and leaves primary graph/rules/revision unchanged. Three repetitions cover full-copy and shared-page branches.

## Allocation and residency

Medians across workers (MiB; allocator counters are process-wide glibc `mallinfo2` values):

| Backend | Sampled peak PSS delta | Peak glibc in-use delta | After release glibc in-use delta | After release PSS delta | After release free-arena delta | PSS delta after `malloc_trim(0)` |
|---|---:|---:|---:|---:|---:|---:|
| Full copy | 360.0 | 358.0 | 0.036 | 193.1 | 192.0 | −0.16 |
| Shared graph pages | 19.3 | 18.3 | 0.030 | 1.28 | 0.39 | −0.24 |

The earlier v1.1 full-copy post-release PSS increase is therefore accounted for by free glibc arena pages in this workload: `uordblks+hblkhd` returns to baseline while free arena bytes rise by about 192 MiB. `malloc_trim(0)` reduces PSS to slightly below baseline because it also releases pre-existing free pages. Shared-page branch allocations also return close to baseline. These are libc process counters; they do not attribute bytes to individual graph objects, and other allocators or platforms may behave differently.

This follow-up strengthens the one-host lifecycle evidence for the recurrence repair path. It does not establish universal CoW reclamation, concurrent throughput, natural-task prevalence, autonomous rule discovery, or general self-improvement.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_ALLOCATOR_RECLAMATION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_allocator_reclamation_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_allocator_reclamation_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_allocator_reclamation_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_allocator_reclamation_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_allocator_reclamation_v1_analysis_20261002.json)
