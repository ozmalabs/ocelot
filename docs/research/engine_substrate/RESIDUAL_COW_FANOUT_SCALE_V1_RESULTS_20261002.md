# Residual CoW fanout scale v1 results

The source-locked 1,000,000-node extension passes all gates across 18 fresh workers: fanout 1/4/16, full-copy/shared-graph-pages branches, and three repetitions per cell. Each branch independently generates the expected candidate and passes held-out scoring; target rules and the host remain unchanged during exploration; one and only one 41-node/2-edge graph residual is returned. The underlying cue and navigation task remain authored.

## Million-node retained fanout

| Backend | Fanout | Validated/package PSS delta | Fork ms per branch | Peak RSS |
|---|---:|---:|---:|---:|
| Full copy | 1 | 8.5 MiB | 139.8 | 4.37 GiB |
| Full copy | 4 | 16.3 MiB | 137.3 | 4.89 GiB |
| Full copy | 16 | 1,457.3 MiB | 184.7 | 6.99 GiB |
| Shared graph pages | 1 | 8.5 MiB | 0.772 | 4.20 GiB |
| Shared graph pages | 4 | 16.6 MiB | 0.633 | 4.22 GiB |
| Shared graph pages | 16 | 41.9 MiB | 0.573 | 4.31 GiB |

At fanout 16, shared pages reduce the measured post-validation PSS delta by about 97.1% versus full copy (41.9 vs 1,457.3 MiB). Relative to the 100k result, the fanout-16 full-copy delta rises about 6.9× as unrelated node count rises 10×; shared-page delta rises about 1.14×. Median fork latency rises from 17.32 to 184.7 ms for full copy and from 0.186 to 0.573 ms for shared pages. At one million nodes, shared-page fork is about 322× faster in this measurement; the absolute latency comparison is host- and fixture-specific. Candidate induction/grounding stays in the same rough range (about 85 ms/branch at fanout 16, compared with 82–103 ms at 100k); held-out scoring is not timed separately.

Peak RSS includes the million-node Python/native fixture itself: about 4.2–4.4 GiB even at fanout one, rising to 6.99 GiB for full-copy fanout 16 and 4.31 GiB for shared pages. PSS after branch drop remains elevated, so it is not a live-allocation measure; the separate 100k glibc probe does not establish allocator behavior at this larger scale. A non-monotonic shared-pages return-stage observation occurs at fanout one (53 MiB PSS delta after return versus 8.5 MiB at the earlier package stage); this reinforces that stages include host-side adoption and allocator residency, and should not be read as branch-retained bytes.

This is evidence that the partial-CoW backend reduces retained memory and fork time for this authored workload through a million unrelated nodes. It is not evidence of linear complexity, full-state CoW, concurrent throughput, 10M–100M-node feasibility, natural-task prevalence, or general self-improvement. Next measure one additional task family and a memory-focused million-node drop/reclamation path, then test concurrent branch work and a larger graph only with an explicit resource budget.

## Artifacts

- [Preregistration](RESIDUAL_COW_FANOUT_SCALE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_residual_cow_fanout_scale_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_residual_cow_fanout_scale_v1.py)
- [Source lock](../../../evaluation/substrate_capability/residual_cow_fanout_scale_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/residual_cow_fanout_scale_v1_20261002.json)
- [Analysis](../../../evaluation/reports/residual_cow_fanout_scale_v1_analysis_20261002.json)
