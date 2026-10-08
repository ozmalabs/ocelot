# Matched-width topology envelope v1.1 results (2026-09-29)

## Result

The corrected, source-locked run completed 144 graphs: four families at q=4/5/6, N=120, and 12 deterministic vertex/edge relabellings per cell. All seven integrity gates pass, including the width-q certificate in every row, no min-fill underestimation, production gate/heuristic agreement, and exact lock match. The q-tree families have an explicit (q+1)-clique lower bound and a width-q elimination certificate; grid widths follow the standard rectangular-grid result and are also certified by the recorded column order.

| q | Topology | Min-fill width counts | False refusals at bound q | Median order time |
|---:|---|---|---:|---:|
| 4 | Grid | 4: 12 | 0/12 | 8.64 ms |
| 4 | q-tree path | 4: 12 | 0/12 | 17.87 ms |
| 4 | q-tree shared-core hub | 4: 12 | 0/12 | 77.06 ms |
| 4 | q-tree random attachment | 4: 12 | 0/12 | 37.37 ms |
| 5 | Grid | 5: 1, 6: 11 | 11/12 | 9.93 ms |
| 5 | q-tree path | 5: 12 | 0/12 | 24.40 ms |
| 5 | q-tree shared-core hub | 5: 12 | 0/12 | 93.54 ms |
| 5 | q-tree random attachment | 5: 12 | 0/12 | 50.25 ms |
| 6 | Grid | 7: 4, 8: 8 | 12/12 | 11.41 ms |
| 6 | q-tree path | 6: 12 | 0/12 | 32.22 ms |
| 6 | q-tree shared-core hub | 6: 12 | 0/12 | 112.10 ms |
| 6 | q-tree random attachment | 6: 12 | 0/12 | 68.70 ms |

At q=5, min-fill falsely refuses 11/12 grids at a bound equal to their certified width, versus 0/12 in each q-tree family. At q=6 it falsely refuses all 12 grids, while all q-tree families return width 6 in every relabelling. These are safe upper-bound refusals, not unsafe accepts. The pattern is not a generic property of all width-q graphs: on these chosen families, the grid's separator shape is specifically harder for min-fill to recover than the chordal q-tree structures.

Ordering time also varies sharply at fixed q and node count: the shared-core q-tree costs much more to order than the grid or path family despite min-fill finding the correct width. Edge counts and degree profiles differ across families, so this is a topology profile rather than a controlled edge-count causal effect. The bag-size histograms and per-case records are retained in raw JSON.

## Gate history and limits

The v1 capture is retained as a failed-gate attempt: a generator error attached new random q-tree vertices to q+1 vertices, yielding higher-width graphs. Those rows are excluded. V1.1 corrects the attachment set to exactly q vertices and reruns the full matrix ([amendment](CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_1_AMENDMENT_20260929.md)).

The four graph families are synthetic; this does not estimate natural-task graph prevalence, learned frame quality, or inference cost. The min-fill gate remains conservative and safe in all measured cases, but this panel establishes that its refusals can be topology-sensitive even when a narrow certificate is available.

## Reproducibility

- Protocol and amendment: [`CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_PREREG_20260929.md`](CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_PREREG_20260929.md), [`v1.1 amendment`](CAN_MATCHED_WIDTH_TOPOLOGY_ENVELOPE_V1_1_AMENDMENT_20260929.md)
- Runner/analyzer: [`can_matched_width_topology_envelope_v1.py`](../../../evaluation/substrate_capability/can_matched_width_topology_envelope_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_matched_width_topology_envelope_v1.py)
- Lock and raw/analysis records: [`lock`](../../../evaluation/substrate_capability/can_matched_width_topology_envelope_v1_1_lock_20260929.json), [`capture`](../../../evaluation/reports/can_matched_width_topology_envelope_v1_1_20260929.json), [`analysis`](../../../evaluation/reports/can_matched_width_topology_envelope_v1_1_20260929_analysis.json)

