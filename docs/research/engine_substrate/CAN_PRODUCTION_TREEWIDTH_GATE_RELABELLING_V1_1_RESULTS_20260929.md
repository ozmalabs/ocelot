# Production treewidth gate relabelling v1.1 results (2026-09-29)

## Result

The source-locked panel completed 72 fresh workers: 12 randomized node/edge insertion orders for each q×32 binary grid, q=1…6. All nine integrity gates pass. Runtime extraction matched all generated factors; the known column-order decomposition had width q in every worker; all 48 accepted MAP results (q=1–4) matched the independent column-DP energy oracle; the 24 q=5/6 cases were refused without returning a state; and `commit=False` left graph states unchanged.

| Known width q | Production accepts | Refuses | Median reported width | Median solver wall time |
|---:|---:|---:|---:|---:|
| 1 | 12/12 | 0/12 | 1 | 1.10 ms |
| 2 | 12/12 | 0/12 | 2 | 3.89 ms |
| 3 | 12/12 | 0/12 | 3 | 9.18 ms |
| 4 | 12/12 | 0/12 | 4 | 22.00 ms |
| 5 | 0/12 | 12/12 | 6 | 20.47 ms |
| 6 | 0/12 | 12/12 | 8 | 35.06 ms |

The randomized ID and insertion orders did not change reported widths or gate decisions in these 12 relabellings per width. At the default bound 4 there were no false refusals within the known-width≤4 cells and no unsafe acceptances above the bound. The q=5/6 refusals are correct for the configured bound; their width estimates are conservative overestimates (6 and 8 versus known widths 5 and 6), but do not change the default decision.

## Limits

The panel varies labels/order on one grid topology and binary pairwise model. It does not test irregular graphs, different elimination tie profiles, alternate factor arities, or natural-task width distributions. Twelve deterministic relabellings do not prove label invariance. The reported wall time combines extraction, treewidth estimation, and inference/refusal; see the grid width-scale study for separated costs.

## Reproducibility

- Protocol and harness amendment: [`CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_PREREG_20260929.md`](CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_PREREG_20260929.md), [`v1.1 amendment`](CAN_PRODUCTION_TREEWIDTH_GATE_RELABELLING_V1_1_AMENDMENT_20260929.md)
- Runner/analyzer: [`can_production_treewidth_gate_relabelling_v1.py`](../../../evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1.py), [`analyzer`](../../../evaluation/substrate_capability/analyze_can_production_treewidth_gate_relabelling_v1.py)
- Lock and raw record: [`lock`](../../../evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1_1_lock_20260929.json), [`capture`](../../../evaluation/reports/can_production_treewidth_gate_relabelling_v1_1_20260929.json), [`analysis`](../../../evaluation/reports/can_production_treewidth_gate_relabelling_v1_20260929_analysis.json)

