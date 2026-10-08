# Where-aware prefix-cost selector v2 results

Date: 2026-10-01

## Result

The frozen beam-8, 128-sample selector with partial evaluation of supported production guard terms selected the exact minimum-work match order on all three workers for the new N=20 retinal support profile. Each worker exhaustively measured all 120 orders. The selected and exact-best order was `[4,0,1,2,3]`, with 44 candidate tests; the installed default also used 44. The estimated work was 5, so the estimator is useful here for ranking but underestimates absolute work substantially.

All eight analyzer gates pass: source lock stability, fresh workers, profile identity, exhaustive order coverage, deterministic decisions, productive guard/effect outcomes, graph parity/fixed-point checks, and selected-versus-exhaustive reconciliation. The index plus selector median was 344–348 μs, of which search accounts for about 259–262 μs.

## Interpretation and limits

This is a positive held-out result after v1's N=16 failure exposed a missing mechanism: v1 ignored `where`, while v2 rejects sampled partial bindings as soon as supported guard atoms become decidable. It establishes that the mechanism fixes this new fixture, not that the selector generalizes. Here the selected order ties the default and the exhaustive optimum, so the result demonstrates no runtime work reduction over current installation behavior. The model's 5-work estimate versus 44 observed tests also warns against treating its score as calibrated cost.

The evidence is one synthetic profile, one production rule, three fresh processes on one host, and a Python prototype. Unsupported guard terms remain unknown. No native matcher integration, diverse task panel, online install policy, or general natural-workload tractability claim follows. Next compare guard-aware selection on preregistered unseen production rule families against default ordering, measure selection overhead against saved closure cost, and only consider engine integration if total charged work improves consistently.

## Reproduction artifacts

- [Preregistration](PREFIX_COST_SELECTOR_V2_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/prefix_cost_selector_v2.py)
- [Analyzer](../../../scripts/analyze_prefix_cost_selector_v2.py)
- [Source lock](../../../evaluation/substrate_capability/prefix_cost_selector_v2_lock_20261001.json)
- [Raw workers](../../../evaluation/reports/prefix_cost_selector_v2_workers_20261001.json)
- [Analysis](../../../evaluation/reports/prefix_cost_selector_v2_20261001.json)
