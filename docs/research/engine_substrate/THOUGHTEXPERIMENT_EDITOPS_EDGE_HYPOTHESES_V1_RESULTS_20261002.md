# Thoughtexperiment edit-operator edge hypotheses v1 results

All gates pass across four fresh source-locked workers and two task families. The runner no longer contains a private AST transform: it enumerates sites through `domains.edit_ops.find_edge_identity_sites` and materializes each candidate through `apply_add_edge_identity_guard`. Each task yields three unique edge-scope hypotheses plus the existing generic composer candidate. The native graph-Term selector sees opaque proposal IDs and two training outcomes per candidate.

In all four recurrence workers, the selector chooses `Not Exists(candidate.has_mint_offer)`; it passes both held-out recurrence episodes. In all four conversation workers, it chooses the message-scoped `Not Exists(InNeighbours(message, responds_to))`; it passes held-out multi-message sequences. Broader observation-, episode-, speech-act-, and agent-scoped guards fail the held-out oracle. Tie/all-wrong controls abstain; primary rules and experiment evidence remain isolated. Source locks, candidate regeneration, and semantic gates pass.

Median canonical candidate generation takes 0.303 ms for recurrence and 0.164 ms for conversation. Scoring all four candidates on two training episodes takes 49.75 ms and 109.45 ms; native selection takes 0.831 ms and 0.494 ms. This indicates the shared edit-operator scan is cheap relative to prediction/scoring on these fixtures. It does not establish a broad task distribution or autonomous discovery: task, target rule, cue, training labels, and oracle remain harness-authored; the panel restricts generation to edge scopes and excludes node-attribute identity sites.

This is a concrete step toward substrate-owned improvement: the benchmark uses the same structural site finder and applier the reflective composer uses, while the graph Term selects a useful hypothesis from evidence. It still does not show the substrate diagnosing a raw residual, choosing which target to repair, or inventing a new operator family.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_EDITOPS_EDGE_HYPOTHESES_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_editops_edge_hypotheses_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1_lock_20261002.json)
- [Training orders](../../../evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_scores_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_analysis_20261002.json)
