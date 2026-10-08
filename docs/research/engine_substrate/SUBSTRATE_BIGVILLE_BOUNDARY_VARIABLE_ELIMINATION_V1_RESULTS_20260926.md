# Bigville induced-boundary variable elimination results

## Result

The 42-case replay passed all source-lock, structure, count, energy, state, and timing gates across three fresh workers; N=15/25; k=0/2/4/6/8/10/12; and three deterministic matching patterns. An independent analyzer reconstructs the min-fill order, every elimination bucket scope and row count, and the exact energy of each returned full state. Boundary-component message MAP agrees with global junction-tree MAP in all cases to 1e-7.

This topology family has induced boundary width 1 at every nonzero k. At k=12, exhaustive boundary search entails 531,441 assignments, while variable elimination evaluates 72 rows (six two-variable buckets, nine rows each). At N=25,k=12, message construction enumerates 4,941 local assignments versus a direct conditional oracle's 1,994,498,073 assignments. The algorithmic count therefore grows with the number of matching pairs rather than with `3^k` for this structure.

Timing does not show a win over global inference. At N=25,k=12, message construction plus boundary elimination is 8.63 ms median versus 7.61 ms for global width-2 JT; at k=0, it is 10.30 ms versus 7.26 ms. N=15 shows the same general pattern with noisy small medians; one k=6 cell is near parity. These paths are Python diagnostics with different setup details, so report timings as measured envelopes, not a production speed claim.

## Interpretation and limits

The evidence supports the conditional algorithmic statement: if interiors have bounded size/interface and the induced boundary factor graph has bounded treewidth, exact elimination work can be polynomial in frame count and exponential in the relevant local widths, not in the total number of boundary variables. This is narrower than saying every small separator gives cheap inference: a dense/high-treewidth boundary can still make elimination exponential.

The topology is a controlled matching of cross-resident factors over authored simulation CANs. The experiment does not estimate natural task boundary width, discover learned frames, execute native boundary messages, measure memory at large scale, or show that partition discovery plus message scheduling beats the existing global width-2 solver. The next gate should increase boundary interaction width and include at least one connected natural task graph before making broader locality claims.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_BIGVILLE_BOUNDARY_VARIABLE_ELIMINATION_PREREG_20260926.md)
- Runner: [`substrate_bigville_boundary_variable_elimination_v1.py`](../../../scripts/substrate_bigville_boundary_variable_elimination_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_boundary_variable_elimination_v1.py`](../../../scripts/analyze_substrate_bigville_boundary_variable_elimination_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/bigville_boundary_variable_elimination_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_bigville_boundary_variable_elimination_v1_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_bigville_boundary_variable_elimination_v1_analysis_20260926.json)
