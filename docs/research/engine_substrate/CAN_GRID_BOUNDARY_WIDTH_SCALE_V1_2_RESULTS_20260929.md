# CAN grid boundary-width scale v1.2 results (2026-09-29)

## Outcome

The corrected source-locked sweep completed 54 fresh workers across q=1–6 variables per column, lengths m=32/128/512, and three replicates per cell. All eight gates pass: extraction parity, both exact junction-tree MAP routes matching the independent column dynamic program, expected fixed-order bag size q+1, valid min-fill width/bag reporting, complete cells, and exact pre/post input-lock agreement.

The table reports medians. Junction-tree calls include Python `tracemalloc` instrumentation; process RSS is separately recorded in the raw workers.

| Grid width q | Length m | Nodes | Min-fill width | JT with min-fill (ms) | JT with column order (ms) | Min-fill ordering (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 32 | 32 | 1 | 2.7 | 2.5 | 0.5 |
| 1 | 128 | 128 | 1 | 10.3 | 12.2 | 4.5 |
| 1 | 512 | 512 | 1 | 42.6 | 41.5 | 72.7 |
| 2 | 32 | 64 | 2 | 8.9 | 8.7 | 1.6 |
| 2 | 128 | 256 | 2 | 36.6 | 36.3 | 25.1 |
| 2 | 512 | 1,024 | 2 | 150.7 | 149.6 | 418.2 |
| 3 | 32 | 96 | 3 | 27.5 | 25.0 | 3.8 |
| 3 | 128 | 384 | 3 | 109.1 | 106.3 | 61.3 |
| 3 | 512 | 1,536 | 3 | 479.6 | 439.4 | 1,030.6 |
| 4 | 32 | 128 | 4 | 67.0 | 67.6 | 9.6 |
| 4 | 128 | 512 | 4 | 286.3 | 284.5 | 160.7 |
| 4 | 512 | 2,048 | 4 | 1,106.0 | 1,220.2 | 2,663.0 |
| 5 | 32 | 160 | 6 | 147.8 | 180.1 | 15.6 |
| 5 | 128 | 640 | 6 | 620.4 | 783.8 | 296.2 |
| 5 | 512 | 2,560 | 6 | 2,487.6 | 3,197.0 | 5,053.6 |
| 6 | 32 | 192 | 8 | 341.3 | 480.8 | 29.0 |
| 6 | 128 | 768 | 8 | 1,451.9 | 1,935.6 | 514.0 |
| 6 | 512 | 3,072 | 8 | 6,024.8 | 7,996.1 | 8,484.8 |

At fixed q, increasing m 16-fold raises exact-inference time roughly 16–18-fold at the endpoints, consistent with linear-in-length behavior over this finite range. At m=512, min-fill-ordered inference grows from 42.6 ms at q=1 to 6.02 s at q=6 (141×), while graph size grows 6×. The independent column DP's operation count rises from 2,046 to 2,093,120. These observations support the expected width-sensitive cost profile on this family; they are not asymptotic proofs.

Min-fill finds the known grid width exactly through q=4, then overestimates by one at q=5 and by two at q=6 (reported widths 6 and 8). The known column-major elimination order retains bag size q+1 throughout and is exact against the same oracle. At the largest cells, heuristic ordering itself costs 5.05 s (q=5) and 8.48 s (q=6), so separator/order discovery can exceed inference cost. This fixed column ordering is supplied by the synthetic generator and does not measure discovering natural frames.

## Limits and disclosed gate history

The v1.1 complete capture is retained as a failed-gate run: its original gate incorrectly required greedy min-fill to return an optimal width. It passed extraction and both MAP oracles in all workers; the fixed-order bag condition passed in all 54, and only the heuristic-width equality check failed in 18. V1.2 changes that gate, records heuristic overhead instead, and reruns the full matrix ([v1.1 amendment](CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_1_AMENDMENT_20260929.md), [v1.2 amendment](CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_2_AMENDMENT_20260929.md)).

This is a synthetic binary-grid envelope with a supplied separator. It does not establish that natural task graphs are decomposable, that frame discovery is cheap, or that other engines/factor families share these numbers.

## Reproducibility

- Protocol: [`CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_PREREG_20260929.md`](CAN_GRID_BOUNDARY_WIDTH_SCALE_V1_PREREG_20260929.md)
- Runner/analyzer: [`can_grid_boundary_width_scale_v1.py`](../../../evaluation/substrate_capability/can_grid_boundary_width_scale_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_grid_boundary_width_scale_v1.py)
- V1.2 input lock: [`lock`](../../../evaluation/substrate_capability/can_grid_boundary_width_scale_v1_2_lock_20260929.json)
- Raw capture and analysis: [`capture`](../../../evaluation/reports/can_grid_boundary_width_scale_v1_2_20260929.json), [`analysis`](../../../evaluation/reports/can_grid_boundary_width_scale_v1_2_20260929_analysis.json)

