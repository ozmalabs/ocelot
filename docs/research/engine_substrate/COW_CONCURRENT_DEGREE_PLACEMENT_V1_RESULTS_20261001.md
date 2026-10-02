# Concurrent CoW degree and target-placement v1 results

The source-locked panel completed **384 waves forming 192 shared-snapshot/eager-copy pairs** across path, regular-four, star, and grid graphs; 10k/50k nodes; 1%/10% target writes; four target policies; and three counterbalanced repetitions. All 64 scenario cells pass full write and branch-edge checks, exact paired branch-ID parity, sibling cancellation/isolation, primary and later-fork invariants, and zero mutation-adjusted post-drop allocation residual. Every cell also has less total live requested allocation and a faster median wave under the shared snapshot path; the result remains synthetic and host-specific.

The main result is that **page placement and degree exposure are separate cost drivers**. Examples at N=50,000, fanout 16, and 10% writes:

| Graph and target policy | Selected target out-degree summary (min / upper median / max / sum) | Shared total live delta (MiB) | Shared mutation increment over fork-only (MiB) | Shared wave (ms) |
|---|---:|---:|---:|---:|
| Path, clustered | 1 / 1 / 1 / 5,000 | 50.4 | 44.1 | 34.1 |
| Path, evenly spread | 1 / 1 / 1 / 5,000 | 117.1 | 110.7 | 90.7 |
| Regular-four, clustered | 4 / 4 / 4 / 20,000 | 62.0 | 46.6 | 36.4 |
| Regular-four, evenly spread | 4 / 4 / 4 / 20,000 | 128.7 | 113.2 | 90.7 |
| Star, clustered | 0 / 0 / 0 / 0 | 34.5 | 19.2 | 22.8 |
| Star, evenly spread | 0 / 0 / 49,999 / 49,999 | 101.2 | 85.9 | 81.2 |
| Star, lowest out-degree | 0 / 0 / 0 / 0 | 38.5 | 23.2 | 25.4 |
| Star, highest out-degree | 0 / 0 / 49,999 / 49,999 | 38.5 | 23.2 | 24.8 |
| Grid, lowest out-degree | 0 / 2 / 2 / 9,552 | 73.5 | 64.2 | 47.4 |
| Grid, highest out-degree | 2 / 2 / 2 / 10,000 | 53.4 | 44.1 | 33.3 |

The regular-four contrast holds degree fixed and shows that spreading writes across the paged graph costs more even when every selected node has the same out-degree. The star comparison shows high-degree placement also matters: the hub-including spread policy allocates and runs substantially above the clustered leaf-only case. For the same star high-degree target set, `high_out_degree` is much cheaper than `spread`; this indicates layout locality can matter in addition to the selected degree multiset. Grid low-degree targets touch more allocation than high-degree targets here, showing that local degree alone does not predict page-copy cost. Uniform-degree graphs make low/high selection identical by design and act as a control.

Across all 64 cells, shared snapshot total-live allocation remains below eager copy (ratios 1.73×–7.80×), and median wave time is lower in 64/64 cells. These are complete wave costs including concurrent fork, write work, synchronization, cancellation, and cleanup. Mutation-only increments above the fork-only control can still be much larger for widely spread writes; the total advantage comes from avoiding eager duplication of untouched base state. The allocator tracks requested Rust payload bytes, not RSS/PSS or allocator metadata. Three repeats on one host, four authored topologies, one payload size, and deterministic target rules do not establish natural-task prevalence or a scaling law.

## Reproduction artifacts

- [Preregistration](COW_CONCURRENT_DEGREE_PLACEMENT_V1_PREREG_20261001.md)
- [Rust fixture](../../../evaluation/substrate_capability/fixtures/cow_concurrent_degree_placement/src/main.rs)
- [Runner](../../../evaluation/substrate_capability/cow_concurrent_degree_placement_v1.py)
- [Independent analyzer](../../../scripts/analyze_cow_concurrent_degree_placement_v1.py)
- [Raw source-locked capture](../../../evaluation/reports/cow_concurrent_degree_placement_v1.json)
- [Analysis](../../../evaluation/reports/cow_concurrent_degree_placement_v1_analysis.json)
