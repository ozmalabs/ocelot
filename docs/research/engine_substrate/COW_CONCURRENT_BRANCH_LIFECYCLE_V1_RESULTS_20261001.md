# Concurrent CoW branch lifecycle v1 results

The native Rust panel completed **60 branch waves forming 30 backend pairs**: 10k/50k-node bases × fanout 1/4/16 × shared-snapshot/eager-copy backends × five repetitions. Backend order is counterbalanced by repetition (see [amendment 3](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_3_20261001.md)). The instrumented worker verifies `ExperimentSnapshot` and `Substrate` are `Send + Sync`, forks and mutates from multiple Rust threads, cancels half the branches while siblings remain live, and compares branch IDs with the eager control.

All semantic gates pass in every row: branch-local writes, primary isolation, survivor validity after cancellation, and unchanged later forks. The independent analyzer confirms matched branch IDs across backends and zero mutation-adjusted allocation residual after drop in every row. Raw post-join allocator deltas do not equal zero: the fork/drop/no-write control is consistently -80/-176/-560 bytes at fanout 1/4/16. Subtracting this matched lifecycle delta gives exactly zero for the mutated arm, so the measured writes leave no additional live Rust allocation bytes after their branches are dropped.

| Base nodes | Fanout | Backend | Median all-live delta (MiB) | Median after cancelling half (MiB) | Median full wave (ms) |
|---:|---:|---:|---:|---:|---:|
| 10,000 | 1 | shared snapshot | 0.062 | 0.062 | 0.276 |
| 10,000 | 1 | eager copy | 0.995 | 0.995 | 3.648 |
| 10,000 | 4 | shared snapshot | 0.248 | 0.125 | 0.439 |
| 10,000 | 4 | eager copy | 3.980 | 1.990 | 4.560 |
| 10,000 | 16 | shared snapshot | 0.993 | 0.498 | 1.849 |
| 10,000 | 16 | eager copy | 15.922 | 7.963 | 11.943 |
| 50,000 | 1 | shared snapshot | 0.215 | 0.215 | 0.811 |
| 50,000 | 1 | eager copy | 4.883 | 4.883 | 11.750 |
| 50,000 | 4 | shared snapshot | 0.858 | 0.430 | 1.376 |
| 50,000 | 4 | eager copy | 19.536 | 9.766 | 13.614 |
| 50,000 | 16 | shared snapshot | 3.434 | 1.719 | 4.126 |
| 50,000 | 16 | eager copy | 78.136 | 39.040 | 37.559 |

These figures include thread startup, synchronization, branch creation, one branch-local node, and cleanup. They are one-host measurements on synthetic isolated-node graphs, not a general speed law or serving result. The allocator records requested Rust allocation bytes, not allocator metadata or RSS/PSS. Matched fork/drop controls are essential: the initial diagnostic showed a 24-byte-per-worker raw offset; the confirmatory protocol now controls for thread-only and same-backend fork/drop lifecycle before attributing retained allocations to branch mutation.

## Reproduction artifacts

- [Preregistration](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_PREREG_20261001.md)
- [Amendment: thread lifecycle control](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_20261001.md)
- [Amendment 2: fork/drop control](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_2_20261001.md)
- [Amendment 3: counterbalanced order](COW_CONCURRENT_BRANCH_LIFECYCLE_V1_AMENDMENT_3_20261001.md)
- [Rust probe](../../../evaluation/substrate_capability/fixtures/cow_concurrent_lifecycle/src/main.rs)
- [Runner](../../../evaluation/substrate_capability/cow_concurrent_branch_lifecycle_v1.py)
- [Independent analyzer](../../../scripts/analyze_cow_concurrent_branch_lifecycle_v1.py)
- [Raw source-locked capture](../../../evaluation/reports/cow_concurrent_branch_lifecycle_v1.json)
- [Analysis](../../../evaluation/reports/cow_concurrent_branch_lifecycle_v1_analysis.json)
