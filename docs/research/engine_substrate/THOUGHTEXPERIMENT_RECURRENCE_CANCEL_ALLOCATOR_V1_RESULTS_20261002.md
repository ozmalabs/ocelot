# Thoughtexperiment recurrence cancellation allocator v1 results

All six fresh-process workers pass the recurrence survivor oracle and host-isolation gates. Eight million-node branches are locally patched, four are released before closure, and the four survivors each emit one offer for 64 candidates and reach a zero-progress fixed point. The allocator probe samples glibc `mallinfo2` and Linux PSS at baseline, after half cancellation, after all release, and after `malloc_trim(0)`.

## Full-copy and shared-page allocator state

Medians across three workers per backend (MiB deltas relative to each worker's fixture baseline unless noted):

| Backend | After all released: in-use Δ | After all released: free-arena Δ | After all released: PSS Δ | After trim: PSS Δ |
|---|---:|---:|---:|---:|
| Full copy | 0.08 | 1,617.4 | 1,619.0 | 126.2 |
| Shared graph pages | 0.07 | 9.5 | 10.5 | 7.3 |

For full copy, the large post-release PSS elevation is not live glibc-accounted branch allocation in these workers: `uordblks+hblkhd` returns within 0.08 MiB of baseline while glibc free-arena bytes rise by about 1.62 GiB. `malloc_trim(0)` reduces PSS by about 1.49 GiB, leaving it 126 MiB above baseline. The free-arena counter remains high after trim even as resident pages are released, so allocator in-use bytes and resident pages describe different things. Shared pages also return in-use bytes close to baseline; their residual PSS and free-arena increases are much smaller.

These counters are process-wide and glibc/Linux-specific; they do not identify individual graph allocations or guarantee behavior under another allocator/runtime. `malloc_trim` can also release free pages that predate the experiment. This establishes cancellation/drop allocator behavior for one million-node synthetic recurrence task on this host, not a general lifecycle theorem or a natural-workload success rate.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_CANCEL_ALLOCATOR_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_cancel_allocator_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_cancel_allocator_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_allocator_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_cancel_allocator_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_cancel_allocator_v1_analysis_20261002.json)
