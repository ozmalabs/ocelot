# Residual CoW allocator reclamation v1 results

Six fresh glibc/Linux workers measure fanout 16 at a 100,000-node host: three full-copy and three shared-graph-pages. All prior residual-workflow gates pass, including candidate utility, exact one-residual return, parent isolation, host rule-store preservation, and source stability. `mallinfo2` samples are available at all six operation stages and `malloc_trim(0)` succeeds in every worker.

## Allocated bytes versus residency

`glibc_inuse` is `uordblks + hblkhd` from `mallinfo2`, in MiB. Median values are:

| Backend | Host baseline | All branches validated | One residual returned | Branches dropped |
|---|---:|---:|---:|---:|
| Full copy | 25.85 | 340.91 | 341.19 | 26.33 |
| Shared graph pages | 25.84 | 64.39 | 64.67 | 26.33 |

The allocated-byte measure falls by 314.58 MiB for full copy and 38.07 MiB for shared graph pages between all-branches-live and after-drop states, returning to within about 0.5 MiB of the host baseline in both arms. This resolves the earlier PSS ambiguity for glibc-accounted allocations: the branches' allocations are freed even though the process retains many mapped/free pages immediately after drop.

Before trimming, median PSS remains 347.05 MiB above baseline for full copy and 71.66 MiB above baseline for shared pages. `malloc_trim(0)` returns 1 in all workers and then PSS is 113.43/112.41 MiB below the respective baselines. Trimming releases more memory than the branch-specific increase because the baseline process itself held reusable glibc arena pages. Therefore the post-trim negative delta is not a negative branch footprint or a fair before/after reclamation ratio. It demonstrates that glibc could return retained pages to the kernel in this process after the branches were dropped.

## Scope and limits

This is one glibc host and one measured residual workflow. `mallinfo2` reports glibc allocator totals, not per-object ownership; Python small-object pools and any non-glibc/custom allocation paths may not be attributed precisely. `malloc_trim` is process-wide and also releases pre-existing free arenas. The result shows that elevated post-drop PSS did not correspond to continued glibc-accounted branch allocations in these workers, but it does not establish universal reclamation, concurrent lifecycle safety, portability, or memory bounds for arbitrary substrate state.

## Artifacts

- Protocol: [preregistration](RESIDUAL_COW_ALLOCATOR_RECLAMATION_V1_PREREG_20261002.md)
- Runner: [measurement wrapper](../../../evaluation/substrate_capability/measure_residual_cow_allocator_reclamation_v1.py)
- Analyzer: [independent gate checker](../../../evaluation/substrate_capability/analyze_residual_cow_allocator_reclamation_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/residual_cow_allocator_reclamation_v1_lock_20261002.json)
- Raw workers: [capture](../../../evaluation/reports/residual_cow_allocator_reclamation_v1_20261002.json)
- Analysis: [gate results](../../../evaluation/reports/residual_cow_allocator_reclamation_v1_analysis_20261002.json)
