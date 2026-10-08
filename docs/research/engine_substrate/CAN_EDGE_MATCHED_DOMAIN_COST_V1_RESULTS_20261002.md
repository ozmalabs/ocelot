# Edge-matched exact-inference domain cost v1 results (2026-10-02)

## Outcome

All 36 fresh workers pass the capture gates, including paired fixture identity, exact runtime extraction, certified width, both MAP orders against the independent generic factor-table oracle, direct returned-state rescoring, supported vocabulary, no mutation, and source/native lock equality. Independent analysis passes 55/55 checks.

Certified-order junction-tree medians and the ternary/binary runtime multiplier are:

| q | Family | Binary JT | Ternary JT | Ternary / binary | Traced-memory multiplier |
|---:|---|---:|---:|---:|---:|
| 4 | Grid | 63.8 ms | 434 ms | 6.81× | 4.66× |
| 4 | Sparse partial q-tree | 28.3 ms | 125 ms | 4.41× | 1.82× |
| 5 | Grid | 138 ms | 1.46 s | 10.51× | 7.60× |
| 5 | Sparse partial q-tree | 36.8 ms | 286 ms | 7.79× | 2.30× |
| 6 | Grid | 276 ms | 4.48 s | 16.26× | 12.18× |
| 6 | Sparse partial q-tree | 56.5 ms | 623 ms | 11.02× | 3.10× |

At the same certified q, node count, topology, fields, and couplings, moving from two to three states raises JT time by 4.4–16.3×; the multiplier grows with q and is larger on grids. Traced-memory multipliers range from 1.8× to 12.2×. This is consistent with the measured bag/separator profile: the grid has many bags near maximum size, while the sparse q-tree contains many smaller bags. It is not a fitted asymptotic law. Min-fill returns exact q on every q-tree but overestimates the grid widths by one at q=5 and q=6 in all replicates, so a min-fill width-q refusal gate rejects valid certified grids.

## Limits

These are synthetic binary/ternary pairwise models at N=120, q≤6, with three replicates per cell on one host. They measure the cost effect of the two supported domains, not natural graph/domain prevalence, higher-width ternary behavior beyond q=6, learned cut discovery, or end-to-end task cost. The q=6 ternary grid median is already 4.48 s at N=120, so multi-state exact inference has a materially narrower practical envelope than binary inference on this host.

## Reproduction artifacts

- [Preregistration](CAN_EDGE_MATCHED_DOMAIN_COST_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/can_edge_matched_domain_cost_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_can_edge_matched_domain_cost_v1.py)
- [Source lock](../../../evaluation/substrate_capability/can_edge_matched_domain_cost_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/can_edge_matched_domain_cost_v1_20261002.json)
- [Analysis](../../../evaluation/reports/can_edge_matched_domain_cost_v1_20261002_analysis.json)
