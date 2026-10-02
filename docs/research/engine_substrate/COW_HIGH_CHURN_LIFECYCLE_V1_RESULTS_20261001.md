# High-churn CoW branch lifecycle v1 — results

The source-locked native capture completed **200 measured waves**: 10k/50k-node bases × fanout 4/16 × shared-snapshot/eager-copy backends × 25 waves. One primary and reusable snapshot stayed alive across all waves in each size/fanout cell. All 200 semantic and primary-isolation gates pass; branch-added NodeIDs match exactly in all 100 shared/eager pairs; every new fork from the retained snapshot preserves the base; and every mutation wave returns to its backend-matched no-write fork/drop allocator control. No post-drop residual accumulated across repeated waves.

| Base nodes | Fanout | Shared median wave | Eager median wave | Eager/shared time | Shared live allocation | Eager live allocation | Eager/shared allocation |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 4 | 0.405 ms | 3.497 ms | 8.64× | 0.25 MiB | 3.98 MiB | 16.04× |
| 10,000 | 16 | 1.396 ms | 10.686 ms | 7.66× | 0.99 MiB | 15.92 MiB | 16.04× |
| 50,000 | 4 | 1.281 ms | 16.858 ms | 13.16× | 0.86 MiB | 19.53 MiB | 22.75× |
| 50,000 | 16 | 3.963 ms | 33.927 ms | 8.56× | 3.43 MiB | 78.14 MiB | 22.75× |

The measured wave includes concurrent worker creation, synchronization, branch mutation, cancellation, and drop. Allocation is live Rust `System`-allocator requested payload sampled while branches are live, adjusted against the matching no-write branch wave; it excludes allocator metadata and resident-page accounting. The results support repeated native snapshot/fork/drop as useful isolation infrastructure under this synthetic node-only workload. They do not establish natural-task prevalence, full-Substrate RSS/PSS behavior, concurrent commit safety, a serving adapter, or a universal latency/memory advantage. The eager comparison materializes the full branch state, while the shared path preserves the reusable base.

See the [preregistration](COW_HIGH_CHURN_LIFECYCLE_V1_PREREG_20261001.md), [source-locked runner](../../../evaluation/substrate_capability/cow_high_churn_lifecycle_v1.py), [independent analyzer](../../../scripts/analyze_cow_high_churn_lifecycle_v1.py), [raw capture](../../../evaluation/reports/cow_high_churn_lifecycle_v1.json), and [analysis](../../../evaluation/reports/cow_high_churn_lifecycle_v1_analysis.json).
