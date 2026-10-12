# Thoughtexperiment A8 proposal bridge v1.3 — held-out utility with digest prediction failure

**Date:** 2026-10-02  
**Status:** Scoring completed; one preregistered prediction failed, so this is not a full preregistered pass.

## Integrity and attribution

The source lock covers 37 entries, including the loaded native binary. Canonical clause parity passed for all three composer rules after firing; negative controls rejected changed operators, guard literals, effect literals, and effect ordering. The fresh four-worker order capture has stable source hashes and no held-out outcomes. All four prompted calls were graph-served and emitted `flip_comparison` variants for `hop_descend_gradient` while preserving the target. All four no-cue calls were graph-served and abstained. The score-worker source-control preflight succeeded and the score file binds the frozen orders.

## Outcomes

The graph proposal passed both held-out directions in all four workers (4/4). It produced valid receipts and preserved each primary graph. The six host reference candidates per worker were all scored: one per worker passed (`flip_comparison`), while the five alternatives failed. The source-rule control passed and the fault-rule control failed in each worker. The unprompted composer abstained in all four workers. The analyzer's integrity, source-stability, receipt, target-preservation, held-out-oracle, control, and cost-reconciliation checks passed.

One preregistered prediction failed: the graph proposal's normalized digest did not match the host `flip_comparison` candidate. A direct structural comparison found the generated rules equal after removing the rule name and engine-generated `content_hash`, `revision`, and `rule_uid` metadata. The preregistered digest function removes the name but retains those metadata fields, so it reports distinct candidates. Preserve this as a failed digest prediction; the existing analysis therefore includes errors despite the graph proposal's held-out utility passing. Do not reinterpret it as a full protocol pass.

Median measured prompted-selection cost was 136.8 ms versus 78.3 ms for the host default prefix; the graph route was slower on this fixture. Median exhaustive host audit cost was 125.2 ms. These costs include the protocol's recorded common task setup and candidate-trial accounting as specified by the analyzer; they do not estimate natural-task acquisition cost.

## Interpretation and artifacts

This is direct evidence that a graph-authored, cue-conditioned A8 proposal can reach the Thoughtexperiment evaluator and pass this authored navigation task, while the graph path abstains with the cue removed. It does not show autonomous diagnosis, proposal diversity, net search-effort or economic benefit, natural-task prevalence, broad self-improvement, or general capability. The graph proposal did not reduce measured selection cost relative to host default ordering.

Artifacts: [v1.3 amendment](THOUGHTEXPERIMENT_A8_PROPOSAL_BRIDGE_V1_3_AMENDMENT_20261002.md); [source lock](../../../evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_3_lock_20261002.json); [orders](../../../evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_3_orders_20261002.json); [scores](../../../evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_3_scores_20261002.json); [analysis](../../../evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_3_analysis_20261002.json); [runner](../../../evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_3.py); [analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_a8_proposal_bridge_v1_3.py).
