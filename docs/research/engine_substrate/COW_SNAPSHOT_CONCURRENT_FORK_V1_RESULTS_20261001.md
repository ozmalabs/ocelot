# Concurrent reusable snapshot fork v1 results

Date: 2026-10-01

## Result

The immutable Rust `ExperimentSnapshot` compiles with `Send + Sync` bounds and is shared as an `Arc` across native worker threads. The paired panel completed all 9 size × fanout cells, with five alternating serial/concurrent repeats per cell. All 7 analyzer gates passed, including source/binary fingerprints, the full schedule, and primary, branch, and later-fork isolation.

Median total fork-plus-one-node-write batch times were:

| Base graph nodes | Fanout | Serial | Concurrent | Serial / concurrent | Concurrent paired wins |
|---:|---:|---:|---:|---:|---:|
| 771 | 1 | 22 μs | 55 μs | 0.40× | 0/5 |
| 771 | 4 | 59 μs | 91 μs | 0.65× | 0/5 |
| 771 | 16 | 156 μs | 256 μs | 0.61× | 0/5 |
| 10,771 | 1 | 70 μs | 117 μs | 0.60× | 0/5 |
| 10,771 | 4 | 262 μs | 173 μs | 1.51× | 5/5 |
| 10,771 | 16 | 1,199 μs | 433 μs | 2.77× | 5/5 |
| 50,771 | 1 | 602 μs | 545 μs | 1.10× | 3/5 |
| 50,771 | 4 | 1,948 μs | 576 μs | 3.38× | 5/5 |
| 50,771 | 16 | 5,026 μs | 1,175 μs | 4.28× | 5/5 |

Snapshot capture medians were 2.8–7.4 μs through 10,771 nodes and 27–39 μs at 50,771 nodes in this Rust fixture.

## Interpretation and limits

The snapshot can be safely shared across Rust threads for concurrent branch creation, and each branch can mutate independently while the primary and captured base remain unchanged. Concurrent execution loses at small sizes/fanouts, where thread dispatch and synchronization dominate. It wins consistently at fanout 4 and 16 on the two larger graphs, reaching 4.28× at 50,771 nodes and fanout 16.

This is native Rust branch fork plus one inserted node, not concurrent rule execution, mutation of one shared live `Substrate`, thoughtexperiment throughput, or a natural workload. It uses isolated-node synthetic graphs on one host and five repeats per cell. The result supports thread-safe snapshot sharing and identifies a scale/fanout crossover; it does not establish universal parallel speedup, cancellation semantics, bounded memory under contention, or compatibility with a serving system.

## Reproduction artifacts

- [Preregistration](COW_SNAPSHOT_CONCURRENT_FORK_V1_PREREG_20261001.md)
- [Python runner](../../../evaluation/substrate_capability/cow_snapshot_concurrent_fork_v1.py)
- [Rust probe source](../../../evaluation/substrate_capability/fixtures/cow_snapshot_threads/src/main.rs)
- [Cargo lockfile](../../../evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.lock)
- [Raw capture](../../../evaluation/reports/cow_snapshot_concurrent_fork_v1.json)
- [Analysis](../../../evaluation/reports/cow_snapshot_concurrent_fork_v1_analysis.json)
