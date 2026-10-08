# Edge-matched width-q topology results v1 (2026-09-29)

## Result

The locked run completed 72 cases: grids and sparse partial q-trees at q=4/5/6, N=120, with 12 deterministic relabellings per paired cell. All seven integrity gates passed. Each grid and sparse partial q-tree pair has exactly the same node and edge count (206 at q=4, 211 at q=5, 214 at q=6). Both have width-q certificates; the partial q-trees retain a (q+1)-clique, establishing the matching lower bound. Min-fill never underestimates, and the production bound-q result matches its reported upper bound.

| q | Topology | Min-fill width counts | False refusals at bound q | Median ordering time |
|---:|---|---|---:|---:|
| 4 | Grid | 4: 12 | 0/12 | 8.96 ms |
| 4 | Sparse partial q-tree | 4: 12 | 0/12 | 11.59 ms |
| 5 | Grid | 5: 1, 6: 11 | 11/12 | 10.32 ms |
| 5 | Sparse partial q-tree | 5: 12 | 0/12 | 12.20 ms |
| 6 | Grid | 7: 4, 8: 8 | 12/12 | 11.47 ms |
| 6 | Sparse partial q-tree | 6: 12 | 0/12 | 13.25 ms |

The width-overestimation difference persists after matching both node and edge counts. It also persists when both families are flagged non-chordal by the preregistered MCS diagnostic (descriptive only, not a gate). Thus the earlier grid-versus-chordal-q-tree contrast is not explained solely by edge count or chordality in these fixtures. Min-fill remains a safe upper bound, but at q=5/6 its production gate falsely refuses many graphs whose supplied decomposition proves width q.

## Limits

The two graph families still differ in degree distribution, geometry, and separator placement; matching N and E does not isolate one causal graph feature. The 12 relabellings per cell are deterministic, and neither family estimates natural task prevalence. No junction-tree message-passing run was included here: the result concerns decomposition and the width gate. The MCS chordality flag is exploratory and not independently adjudicated.

## Reproducibility

- Protocol: [`CAN_EDGE_MATCHED_WIDTH_TOPOLOGY_V1_PREREG_20260929.md`](CAN_EDGE_MATCHED_WIDTH_TOPOLOGY_V1_PREREG_20260929.md)
- Runner/analyzer: [`can_edge_matched_width_topology_v1.py`](../../../evaluation/substrate_capability/can_edge_matched_width_topology_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_edge_matched_width_topology_v1.py)
- Lock/raw/analysis: [`lock`](../../../evaluation/substrate_capability/can_edge_matched_width_topology_v1_lock_20260929.json), [`capture`](../../../evaluation/reports/can_edge_matched_width_topology_v1_20260929.json), [`analysis`](../../../evaluation/reports/can_edge_matched_width_topology_v1_20260929_analysis.json)

