# Forest ordering comparison

**Run date:** 2026-09-25  
**Runner:** [can_forest_ordering_comparison.py](../../../scripts/can_forest_ordering_comparison.py)  
**Preregistration:** [CAN_FOREST_ORDERING_COMPARISON_PREREG_20260925.md](CAN_FOREST_ORDERING_COMPARISON_PREREG_20260925.md)  
**Lock:** [can_forest_ordering_lock_20260925.json](../../../evaluation/substrate_capability/can_forest_ordering_lock_20260925.json)  
**Raw report:** [can_forest_ordering_comparison_20260925.json](../../../evaluation/reports/can_forest_ordering_comparison_20260925.json)

## Results

Eight fresh workers compared generic min-fill ordering with a forest-specific leaf-elimination perfect elimination order on runtime-extracted binary paths, at n=256/512/1,024/2,048 (two matched replicates per size). Both orders produced width one and bag size two, and the two junction-tree MAP runs agreed in exact energy on all eight cases.

| Nodes | Min-fill ordering | Leaf ordering | Order speedup | MAP after min-fill | MAP after leaf order |
|---:|---:|---:|---:|---:|---:|
| 256 | 17.98 ms | 0.136 ms | 132× | 2.46 ms | 2.41 ms |
| 512 | 75.70 ms | 0.287 ms | 264× | 5.03 ms | 4.75 ms |
| 1,024 | 294.51 ms | 0.520 ms | 566× | 10.04 ms | 9.80 ms |
| 2,048 | 1,309.15 ms | 1.183 ms | 1,105× | 22.36 ms | 21.74 ms |

The specialized order is linear-time on this forest family and removes the dominant measured setup cost. At n=2,048, ordering plus MAP is about 23 ms with leaf elimination versus 1.33 s with min-fill. These paired timings ran without tracemalloc; the earlier scale table's solver timings included tracemalloc, so compare MAP runtimes within this table. The order speedup is the primary result.

## Limits and follow-up

This is an algorithm comparison on known paths. The runner assumes a forest and rejects cyclic inputs; it does not show that production code can safely recognize or maintain this structural condition, nor does it cover width-two or general bounded-treewidth graphs. Do not replace min-fill globally from this result. Next validate the leaf-order verifier on tree-shaped forests, cycles, and deliberately malformed topology, then compare a guarded dispatch (verified forest → leaf order, otherwise min-fill) on a mixed-width corpus with exact MAP parity and ordering cost included.
