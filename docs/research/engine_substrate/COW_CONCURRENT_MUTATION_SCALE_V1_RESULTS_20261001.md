# Concurrent CoW topology and mutation-density v1 results

The preregistered panel completed **144 branch waves forming 72 paired backend comparisons** across path/star/grid graphs, 10k/50k nodes, 1%/10% edited nodes, and fanout 4/16 (three repeats per cell). Every row passes attribute/edge-write validation, branch-ID parity, primary and later-fork isolation, survivor checks after half-branch cancellation, and exact mutation-adjusted allocation return after drop. The independent analyzer revalidates source hashes and all 24 paired cells.

Across all 24 cells, the shared-snapshot path uses less all-live requested Rust allocation than eager copy (eager/shared ratios 1.73×–3.12×) and has lower median full-wave latency in all 24 cells (1.17×–3.73× lower, descriptive). These are total wave measurements: branch forks, edits, synchronization, and worker lifecycle are included.

At 50k nodes and fanout 16, the interaction between topology, write density, and sharing is visible:

| Topology | Edited nodes | Shared total live delta (MiB) | Eager total live delta (MiB) | Shared mutation increment over fork-only control (MiB) | Eager mutation increment (MiB) | Shared/eager full wave (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Path | 1% (500) | 63.1 | 184.7 | 56.8 | 0.2 | 49.3 / 101.9 |
| Path | 10% (5,000) | 117.1 | 203.7 | 110.7 | 19.3 | 84.4 / 116.5 |
| Star | 1% (500) | 68.4 | 169.2 | 53.1 | 0.8 | 41.8 / 97.5 |
| Star | 10% (5,000) | 101.2 | 175.3 | 85.9 | 6.9 | 78.1 / 107.5 |
| Grid | 1% (500) | 66.2 | 200.3 | 56.8 | 0.2 | 50.2 / 104.6 |
| Grid | 10% (5,000) | 120.1 | 219.3 | 110.8 | 19.3 | 78.9 / 120.8 |

The fork-only-adjusted mutation increment is substantially higher for shared pages at low density because eager-copy has already paid to duplicate the full base during fork; it is not a direct indication that CoW consumes more total memory. At 10% writes, shared mutation cost rises, while shared total live bytes and full-wave latency still remain below eager in these cells. This demonstrates a real write-amplification boundary alongside CoW's lower total branch cost. Star results differ from path/grid, so topology cannot be collapsed to node count alone.

The data are one-host, synthetic directed graphs with a fixed 128-byte payload per edited node and evenly spaced targets. The `System` counter measures requested Rust allocation bytes, not allocator metadata or RSS/PSS. The three-repeat cells are descriptive. They do not establish natural workload prevalence, an asymptotic bound, or serving behavior. The next useful scaling gate should add randomized degree distributions and clustered versus spread targets, then repeat on a second host or with task-generated graph receipts.

## Reproduction artifacts

- [Preregistration](COW_CONCURRENT_MUTATION_SCALE_V1_PREREG_20261001.md)
- [Rust fixture](../../../evaluation/substrate_capability/fixtures/cow_concurrent_mutation_scale/src/main.rs)
- [Runner](../../../evaluation/substrate_capability/cow_concurrent_mutation_scale_v1.py)
- [Independent analyzer](../../../scripts/analyze_cow_concurrent_mutation_scale_v1.py)
- [Raw source-locked capture](../../../evaluation/reports/cow_concurrent_mutation_scale_v1.json)
- [Analysis](../../../evaluation/reports/cow_concurrent_mutation_scale_v1_analysis.json)
