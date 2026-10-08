# Harvest-shape receipt lineage v2 results

**Outcome:** the identity-based owner lookup removed the receipt-dependent shape change. The preregistered nonempty-transfer expectation for `machine_learning` failed because the exact selected donor node is owned by `computer_vision`; that result exposes an earlier false attribution rather than a remaining branch mismatch.

## Panel results

The three-worker full-boot panel passes six of seven gates: distinct workers, stable fixture identity, stable source/seed fingerprints, exact canonical graph equality, complete Direct/receipt target-shape equality, and exactly one owner candidate tied to the selected donor node. Both paths select Concept node 15504 and assign `computer_vision` (21985). Both return zero structural transfers for the machine-learning lineage. The failed gate expected both arms to transfer nonempty output under machine learning; after identity-based attribution, that premise is incorrect.

## Owner-lineage follow-up

A deterministic analysis of the source-locked shape captures passes all six follow-up gates. The same `differentiate()` implementation returns zero transfers for `machine_learning` in both arms and one `scale_cancellation` transfer for `computer_vision` in both arms. Direct and receipt shapes and transfer outputs match exactly. This confirms the selected source identity's owner controls the existing structural applicability gate, and receipt order no longer controls that decision.

The correction is to retain the selected donor's node identity, not to force the old `machine_learning` label. The old name-based map conflated two distinct `batch_normalization` concept nodes and could associate one donor with the other node's owner.

## Limits and next steps

This is a controlled corpus-derived rewire and same-domain counterfactual, not a naturally authored postulate task. It establishes provenance and applicability consistency, but not a user-facing task outcome. Next add an end-to-end held-out fixture whose goal depends on the shape's source lineage, preserve/review source node IDs in harvested shape schema, and replay the relevant receipt task gates. Separately decide whether the now-unused name-keyed helper should be removed or changed to report all owners. The general graph serialization ordering contract remains open.

See [v2 protocol](THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V2_PREREG_20261001.md), [v2 capture](../../../evaluation/reports/thoughtexperiment_harvest_shape_receipt_lineage_v2_raw_20261001.json), [lineage analysis protocol](THOUGHTEXPERIMENT_HARVEST_SHAPE_LINEAGE_OWNER_ANALYSIS_V1_PREREG_20261001.md), and [lineage analysis](../../../evaluation/reports/thoughtexperiment_harvest_shape_lineage_owner_v1_analysis_20261001.json). The failed v2 nonempty-transfer gate is reported explicitly; it is not counted as a pass.
