# Thoughtexperiment targeted commit factorial v1.1 — results

**Date:** 2026-10-01  
**Status:** all 432 paired clean trials and 108 injected-writer cases pass every preregistered correctness gate.

Three fresh workers covered 36 combinations of 256/1,000/5,000 live nodes, 0/2/8 background out-degree, and 1/4/32/128 total hub incident edges. Each cell has 12 paired trials. Four tombstone layouts (`none`, interior-random, trailing, mixed) occur in every cell. The directed circulant gives every non-focal node exactly the assigned number of outgoing background edges, including the hub spokes; the three focal nodes are excluded. This keeps background density independent of aperture. Clean legacy and targeted arms are counterbalanced and each is checked against a complete independent graph oracle. Every paired arm chooses the same added-node ID. All 108 competing-writer injections reject atomically while retaining the competitor and original proposal targets.

## Aggregate paired commit times

Each row pools four aperture levels (48 paired trials). The ratio is the median of per-trial legacy/targeted ratios; win count compares each matched pair.

| Live nodes | Background out-degree | Legacy median (ms) | Targeted median (ms) | Median pair ratio | Targeted wins |
|---:|---:|---:|---:|---:|---:|
| 256 | 0 | 7.63 | 6.19 | 1.28× | 39/48 |
| 256 | 2 | 10.69 | 7.56 | 1.38× | 39/48 |
| 256 | 8 | 20.97 | 7.09 | 2.82× | 48/48 |
| 1,000 | 0 | 11.11 | 6.75 | 1.69× | 44/48 |
| 1,000 | 2 | 21.13 | 6.53 | 3.03× | 47/48 |
| 1,000 | 8 | 59.79 | 8.31 | 6.97× | 48/48 |
| 5,000 | 0 | 32.05 | 7.19 | 4.72× | 48/48 |
| 5,000 | 2 | 99.21 | 8.72 | 11.19× | 48/48 |
| 5,000 | 8 | 324.73 | 15.34 | 21.93× | 48/48 |

The measured saving grows strongly with both node count and background edge density. At 5,000 nodes/out-degree 8, legacy commit is 324.7 ms median versus 15.3 ms targeted; the large difference is consistent with legacy full-graph materialization while targeted reads remain limited to the receipt and a node-slot scan for ID allocation. At 256 nodes/out-degree 0, the improvement is modest and has 39/48 paired wins, showing that gate/assessment and fixed costs remain material at the small/sparse end.

## Aperture slice at 5,000 nodes/out-degree 8

| Hub incident degree | Legacy median (ms) | Targeted median (ms) | Median pair ratio | Targeted wins |
|---:|---:|---:|---:|---:|
| 1 | 292.68 | 14.07 | 20.95× | 12/12 |
| 4 | 334.80 | 12.13 | 25.74× | 12/12 |
| 32 | 335.58 | 17.36 | 19.09× | 12/12 |
| 128 | 347.27 | 18.07 | 18.55× | 12/12 |

Targeted cost rises between degree 4 and degrees 32/128 in this slice, but is not monotonic across all four levels. Each aperture cell has 12 trials on one host; more repeats and another graph topology are needed to resolve this cost surface. Aperture itself changes the explicit hub-edge count while background edge count stays fixed.

The earlier v1 panel is retained as a diagnostic capture, not pooled here: its background graph excluded spokes, so aperture reduced the number of density-eligible nodes. v1.1 fixes that design confound. Even v1.1 remains a synthetic directed-circulant model and one-host measurement, not an asymptotic law or natural-task distribution. The targeted path's `next_live_node_id` scans node slots, so its observed scaling is not constant-time. Next test a second background topology, add more independent hosts/repeats, and repeat with task-generated receipts while retaining the stale-writer and tombstone gates.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_TARGETED_COMMIT_FACTORIAL_V1_1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_targeted_commit_factorial_v1_1.py)
- [Raw three-worker capture](../../../evaluation/reports/thoughtexperiment_targeted_commit_factorial_v1_1.json)
- [Superseded v1 diagnostic protocol](THOUGHTEXPERIMENT_TARGETED_COMMIT_FACTORIAL_V1_PREREG_20261001.md)
- [Superseded v1 diagnostic capture](../../../evaluation/reports/thoughtexperiment_targeted_commit_factorial_v1.json)
