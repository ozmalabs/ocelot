# Edge-matched degree-profile exact inference v1.1 (2026-09-29)

## Result

The corrected 54-worker capture passed all nine integrity gates: complete q/family coverage, matched N/E, width-q certificates, exact factor extraction, agreement of both junction-tree MAP orders with an independent factor-table oracle, no mutation, complete degree fields, and unchanged input lock. The preregistered v1 capture is retained but invalid for degree comparison because its wrapper accidentally dispatched both q-tree labels to the hub generator; the correction and audit trail are in the [v1.1 amendment](CAN_EDGE_MATCHED_DEGREE_PROFILE_V1_1_AMENDMENT_20260929.md).

The experiment compares three synthetic binary pairwise families at N=120: a q-wide grid; a sparse partial q-tree; and a partial q-tree built from a fixed K(q+1) core with extra edges concentrated on the earliest vertices and a persistent hub. Each family is matched to the grid's edge count for that q, and each has a constructive certificate of width q. There are six deterministic replicates per cell. Exact outputs are scored against the original factors and a separately implemented min-sum variable-elimination oracle.

| q | Family | E | Median max degree | Median degree Gini | Min-fill width | Min-fill message entries | Min-fill loop proxy | Min-fill JT (ms) | Certified JT (ms) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | Grid | 206 | 4 | 0.082 | 4 | 1,607 | 6,820 | 57.18 | 64.39 |
| 4 | Sparse partial q-tree | 206 | 34 | 0.470 | 4 | 550 | 3,447 | 30.12 | 28.02 |
| 4 | Hub partial q-tree | 206 | 119 | 0.636 | 4 | 639 | 3,580 | 28.67 | 19.19 |
| 5 | Grid | 211 | 4 | 0.080 | 6 | 2,755 | 12,732 | 112.17 | 136.29 |
| 5 | Sparse partial q-tree | 211 | 36.5 | 0.482 | 5 | 641 | 4,914 | 39.01 | 37.23 |
| 5 | Hub partial q-tree | 211 | 119 | 0.648 | 5 | 897 | 4,656 | 39.98 | 28.81 |
| 6 | Grid | 214 | 4 | 0.076 | 7 | 4,391 | 22,284 | 194.39 | 286.61 |
| 6 | Sparse partial q-tree | 214 | 33.5 | 0.493 | 6 | 745 | 6,780 | 54.49 | 55.48 |
| 6 | Hub partial q-tree | 214 | 119 | 0.655 | 6 | 1,345 | 6,028 | 56.11 | 44.69 |

Values are medians over six workers. The loop proxy is source-aligned but not a hardware-independent operation count. JT times are descriptive Python timings on this host; the certified order can be faster or slower than min-fill.

## Interpretation

At fixed N/E/q, degree profile and separator placement substantially change the elimination profiles. The regular grids require about 2.5–3.3 times as many min-fill message entries as the sparse partial q-trees and run about 1.9–3.6 times slower in these cells. The hub construction's maximum degree is 119, versus 33.5–36.5 for the sparse partial q-trees, but this extreme concentration changes median min-fill JT time only modestly at q=5/6 (about 40/56 ms versus 39/54 ms). The hub's message-entry count rises by 40% at q=5 and 81% at q=6, while elapsed time does not rise proportionally. This is evidence that degree maximum and message-entry total alone do not determine runtime; full profile shape, implementation effects, and timing noise remain relevant.

Min-fill overestimates the certified width on the grids at q=5/6 (6 vs 5; 7 vs 6), but not on either q-tree family. This repeats the topology-sensitive gate behavior under a third degree profile. The experiment supports the practical value of full elimination profiles over max degree or max bag alone for these fixtures. It does not establish a universal runtime model, natural task graph distribution, or learned frame discovery cost.

## Reproducibility

- [Preregistration](CAN_EDGE_MATCHED_INFERENCE_COST_V1_PREREG_20260929.md) and [v1.1 harness correction](CAN_EDGE_MATCHED_DEGREE_PROFILE_V1_1_AMENDMENT_20260929.md)
- [Runner](../../../evaluation/substrate_capability/can_edge_matched_degree_profile_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/can_edge_matched_degree_profile_v1_1_lock_20260929.json)
- [Raw capture](../../../evaluation/reports/can_edge_matched_degree_profile_v1_1_20260929.json)

The corrected runner reuses the inference worker and independent-oracle implementation from the [edge-matched inference cost harness](../../../evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py). The raw record contains per-worker order/profile, factor parity, wall/CPU times, traced Python allocation, and process high-water RSS.
