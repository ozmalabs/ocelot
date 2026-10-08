# Thoughtexperiment full reground scale v1.1 — results

**Date:** 2026-10-01  
**Status:** source-locked balanced factorial; all 45 worker/cell oracle checks pass.

Five fresh workers evaluate every graph-size × deletion-count cell on chain graphs with degree-2 target nodes. All expected proposals survive in every repeat. The table reports the median across the five worker medians and the maximum worker median as a coarse tail descriptor.

| Nodes | Deletion conclusions | Validated incident edges | Median reground | Max worker median |
|---:|---:|---:|---:|---:|
| 1,000 | 1 | 2 | 0.072 ms | 0.072 ms |
| 1,000 | 16 | 32 | 0.756 ms | 0.796 ms |
| 1,000 | 128 | 256 | 5.827 ms | 6.094 ms |
| 10,000 | 1 | 2 | 0.070 ms | 0.072 ms |
| 10,000 | 16 | 32 | 0.766 ms | 1.013 ms |
| 10,000 | 128 | 256 | 6.063 ms | 6.715 ms |
| 50,000 | 1 | 2 | 0.071 ms | 0.073 ms |
| 50,000 | 16 | 32 | 0.756 ms | 0.778 ms |
| 50,000 | 128 | 256 | 5.887 ms | 7.900 ms |

At fixed deletion count, increasing unrelated graph size from 1k to 50k nodes does not increase the median materially in this topology. At fixed graph size, increasing proposals from 1 to 16 to 128 raises median cost from about 0.07 to 0.76 to 5.9–6.1 ms. This is direct evidence that the optimized reground path's measured cost follows the size of the deletion receipt/interface more closely than total unrelated node count, for these chain fixtures. It supports the tractability role of local frames on this specific operation; it does not show how often natural tasks provide such cuts.

The five-worker maximum is noisy in the largest 128-deletion cell (7.900 ms at 50k versus 5.887 ms median), so tail behavior needs more workers/repeats. All cells share one topology and fixed-degree deletion nodes; hub deletion remains much more expensive in v1 because its receipt contains all incident edges. The next gate is seeded randomized sparse topologies and a node/edge attribute conflict oracle, followed by natural-task deletion receipts and complete harness timing.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_FULL_REGROUND_SCALE_V1_1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_full_reground_scale_v1_1.py)
- [Raw five-worker capture](../../../evaluation/reports/thoughtexperiment_full_reground_scale_v1_1.json)
