# Guarded forest ordering with min-fill fallback

**Run date:** 2026-09-25  
**Runner:** [can_guarded_forest_dispatch.py](../../../scripts/can_guarded_forest_dispatch.py)  
**Preregistration:** [CAN_GUARDED_FOREST_DISPATCH_PREREG_20260925.md](CAN_GUARDED_FOREST_DISPATCH_PREREG_20260925.md)  
**Lock:** [can_guarded_forest_dispatch_lock_20260925.json](../../../evaluation/substrate_capability/can_guarded_forest_dispatch_lock_20260925.json)  
**Raw report:** [can_guarded_forest_dispatch_20260925.json](../../../evaluation/reports/can_guarded_forest_dispatch_20260925.json)

## Results

The 66 fresh workers covered paths, balanced binary trees, cycles, ladders, sparse random path-plus-chord graphs at n=32/64/128/256, and cliques at n=8/12, with three replicates per cell. Every graph was constructed in a native Microtheory and recovered exactly by the runtime CAN extractor.

The union-find detector classified all 24 forest controls (paths and trees) as forests and rejected all 42 cyclic controls (cycles, ladders, sparse random graphs, and cliques). For detected forests, the runner selected leaf elimination. For cyclic graphs it reused the same min-fill order already computed for the baseline. The width-4 gate decision was identical for both policies on all 66 cases. It admitted 49 cases and refused 17. Among admitted cases, paired MAP energies and bag widths agreed on all 49.

Selected paired medians below include ordering policy plus MAP when admitted. For a forest, guarded cost is detector + leaf-order construction + MAP; for a cyclic graph, it is detector + min-fill + MAP. Baseline is min-fill + MAP. Over-gate rows have no MAP term and represent a width check/refusal path.

| Family | Nodes | Min-fill width | Baseline total | Guarded total |
|---|---:|---:|---:|---:|
| Path | 256 | 1 | 22.70 ms | 2.36 ms |
| Balanced tree | 256 | 1 | 23.02 ms | 2.37 ms |
| Cycle | 256 | 2 | 24.61 ms | 24.56 ms |
| Ladder | 256 | 2 | 28.55 ms | 28.52 ms |
| Sparse random | 256 | 34 (replicate median) | 63.09 ms | 63.10 ms |
| Clique | 12 | 11 | 0.23 ms | 0.23 ms |

At n=256, guarded dispatch reduced total ordering-plus-MAP time by about 90% on paths and trees. On cyclic structures it added only the forest-detection cost and preserved the min-fill path; the observed difference was small and within timing variation. The sparse random and clique controls were refused by the same width gate, so no exact MAP was attempted for them.

## Interpretation and limits

This supports a benchmark-level policy: a complete edge scan with union-find can distinguish these forest inputs, leaf elimination preserves exact MAP there, and fallback retains the generic min-fill order on cyclic controls. It gives no evidence about how often natural substrate inference graphs are forests, nor whether arbitrary production extraction paths expose all relevant factors to the detector. Timing results are local Python medians on synthetic inputs and are not a production speedup estimate.

The code remains an evaluation harness; no production dispatch API changed. Before integration, validate the same policy on runtime-derived workload graphs and duplicates/self-loop/malformed edge controls, then move the policy behind a single shared ordering interface so the width gate and solver cannot disagree about which order was measured. Keep min-fill fallback and refusal behavior as the baseline.
