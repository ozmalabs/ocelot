# Thoughtexperiment navigation polarity repair v1.1 — results

**Corrected independent review: 16/16 gates pass.** Three fresh, source/native-locked workers each evaluated four held-out cardinal directions. The source `hop_descend_gradient` rule passes all four; its comparison-flipped fault fails all four by choosing the opposite action. Given a graph-resident issue axis whose residual explicitly includes `flip`, the graph-authored composer selects `flip_comparison`, emits a variant of the target rule, and that candidate passes all four cases in every worker.

The unchanged candidate surface emits six variants on the faulted rule. The `flip_comparison` variant passes 4/4; the always-generated match guard and four attribute-key swaps each pass 0/4. The composed rule is structurally identical to the candidate-surface flip modulo its generated name. The target rule in the composer substrate remains unchanged; candidate behavior is evaluated on fresh core+navigation substrates.

| Candidate | Held-out passes (each of 3 workers) |
|---|---:|
| `flip_comparison` | 4/4 |
| `add_match_guard(control)` | 0/4 |
| `swap_term_leaf:_adist->_dist` | 0/4 |
| `swap_term_leaf:_adist->_epoch` | 0/4 |
| `swap_term_leaf:_adist->col` | 0/4 |
| `swap_term_leaf:_adist->flood_epoch` | 0/4 |

This is a third authored correction family with an exact native behavior oracle. It shows the substrate can compose a real edit from a supplied symptom cue and produce a behaviorally correct rule on four held-out states. The cue includes the word `flip`, and the host candidate generator also places the successful flip first; this panel establishes edit utility and graph composition, not a search-cost advantage, autonomous diagnosis, outcome-conditioned learning, or open-ended self-improvement. The new family does not satisfy the separate four-family ranker utility gate.

Two harness defects are disclosed. The first v1 worker attempt failed before scoring because PyO3 `NodeID` does not support `int()`; no v1 capture was written. V1.1 fixes diagnostic serialization and captures all workers. Its first analyzer attempt then failed before scoring because it lacked the workspace import path; the initial analyzer remains unchanged, and a separate corrected reviewer passes 16/16 checks. See the [NodeID amendment](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md) and [analyzer amendment](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_REVIEW_AMENDMENT_20261002.md).

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md)
- [V1.1 amendments](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md), [review amendment](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_REVIEW_AMENDMENT_20261002.md)
- [V1.1 runner](../../../evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py)
- [Initial analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_navigation_polarity_repair_v1_1.py)
- [Corrected independent reviewer](../../../evaluation/substrate_capability/review_thoughtexperiment_navigation_polarity_repair_v1_1.py)
- [V1.1 source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1_lock_20261002.json)
- [V1.1 raw capture](../../../evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_raw_20261002.json)
- [Corrected review](../../../evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_analysis_review_20261002.json)
