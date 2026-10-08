# Copy-on-write branch write density and locality v1 results

## Gates

All **70 fresh-process workers** across 14 size × density × locality cells completed. Every cell has five repeats. Semantic closure, exact output count, fixed point, primary revision/state, later-fork isolation, arm ordering, and unique process checks pass. The analyzer verifies the full preregistered factorial. Two pilot cells were run before the confirmatory panel and are excluded from the capture.

## 50,771-node results

All times are medians; branch fork and closure medians pool the 20 branch observations within each cell. PSS is the median whole-process delta with four branches live.

| Active writes | Layout | CoW fork / closure / concurrent wall (ms) | Eager fork / closure / concurrent wall (ms) | CoW / eager live PSS (MiB) |
|---:|---|---:|---:|---:|
| 1% | contiguous | 0.07 / 1.88 / 2.72 | 12.85 / 0.50 / 15.19 | 24.1 / 36.8 |
| 1% | spread | 0.09 / 3.36 / 4.52 | 12.52 / 0.78 / 15.77 | 34.2 / 39.1 |
| 10% | contiguous | 0.10 / 6.43 / 7.35 | 13.08 / 5.31 / 19.87 | 33.7 / 26.4 |
| 10% | spread | 0.09 / 9.58 / 10.43 | 14.22 / 6.56 / 22.17 | 48.5 / 43.0 |
| 50% | contiguous | 0.11 / 33.88 / 36.74 | 11.81 / 33.73 / 48.24 | 57.5 / 77.5 |
| 50% | spread | 0.11 / 36.73 / 39.02 | 11.49 / 31.83 / 48.70 | 57.6 / 82.5 |
| 100% | contiguous | 0.11 / 68.81 / 73.48 | 11.70 / 69.63 / 83.71 | 74.0 / 61.1 |

The CoW branch fork stays near 0.07–0.11 ms while eager branch fork is about 11.5–14.2 ms at this size. That difference persists in total concurrent wall time: CoW is faster in 34/35 paired worker rows at each graph size. The closure component shows the tradeoff directly. For sparse writes, CoW closure is slower than eager closure, especially when active edges are spread across the ring; at 50% and 100%, closure times are similar. Thus the total time advantage in this fixture comes primarily from avoiding eager full-state copies, not faster rule execution.

Memory does not follow one monotonic density curve. CoW live PSS is below eager at 1% contiguous and 50% writes, but above eager for 10% and 100% contiguous in this panel. Spreading active edges increases CoW closure time at low and medium densities and raises live PSS at 1%/10%; the 50% CoW PSS medians are nearly equal across layouts. The matched 10,771-node results show additional cell-level variation in both time and memory. Treat these as evidence that touched structure and allocator behavior matter, not as a universal locality law.

## What this establishes

This supports CoW as a useful reusable-state capability for repeated branch workloads: it sharply reduces branch-fork cost at 50k nodes and usually lowers total time even when sparse branch closure itself is slower. It also shows that sharing is not free: write locality affects closure cost, and live PSS may favor either backend depending on density. One host, a ring topology, one additive edge rule, four branches, and 14 cells do not establish natural-workload distributions or asymptotic behavior. The rule remains non-`batch_safe`; concurrency is across isolated branches. PSS is process-level and drop samples do not prove exact object reclamation.

This is a graph-native branch result, not a vLLM integration. The future shared-prefix adapter still needs explicit ownership, revision, cancellation, and reclamation semantics; model KV blocks and request scheduling require their own consumer implementation and measurements.

## Artifacts

- [Preregistration](COW_SNAPSHOT_WRITE_DENSITY_LOCALITY_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/cow_snapshot_write_density_locality_v1.py)
- [Rust fixture](../../../evaluation/substrate_capability/fixtures/cow_snapshot_write_density/src/main.rs)
- [Raw source-captured data](../../../evaluation/reports/cow_snapshot_write_density_locality_v1.json)
- [Analysis](../../../evaluation/reports/cow_snapshot_write_density_locality_v1_analysis.json)
- [Analyzer](../../../scripts/analyze_cow_snapshot_write_density_locality_v1.py)
