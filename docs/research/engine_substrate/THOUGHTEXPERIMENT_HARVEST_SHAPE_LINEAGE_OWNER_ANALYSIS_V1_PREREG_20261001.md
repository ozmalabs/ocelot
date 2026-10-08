# Harvest-shape lineage-owner analysis v1 preregistration

**Question.** Given the identity-corrected Direct/receipt shape captured by lineage v2, does the real `differentiate()` gate accept only the exact donor owner's lineage?

## Method and gates

Read the complete three-worker v2 raw capture. Verify its source-stable flag and that the current `domains/implication_harvester.py` and `domains/order_n_postulates.py` hashes match the v2 capture. For each worker, pass the captured Direct and receipt `scale_cancellation` shapes to the actual `differentiate()` function with empty text, `substantive_structural=True`, `structural_max_hops=0`, and identical hop/lineage inputs. Evaluate both `machine_learning` (ID 15483) and `computer_vision` (ID 21985). Require Direct/receipt shape equality, no transfer under machine-learning lineage, one transfer under computer-vision lineage, and identical outputs between arms for both lineages.

## Limits

This is a pure downstream analysis of source-locked full-boot shape captures. It does not repeat the boot or graph rewrite, and it tests a constructed same-domain structural counterfactual rather than a natural postulate task.
