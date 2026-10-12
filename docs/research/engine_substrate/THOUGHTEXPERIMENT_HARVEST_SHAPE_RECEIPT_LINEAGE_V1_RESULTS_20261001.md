# Harvest-shape receipt lineage v1 results

**Result:** receipt ordering propagates into the active `scale_cancellation` shape's source Microtheory metadata while all other measured shape content and whole-graph facts remain equal.

## Gates and observation

Three fresh full-boot workers pass all six gates: stable source/seed fingerprints; the same two target and two owner identities; exact canonical whole-graph equality between Direct and adopted primary; identical selected shape signatures after removing only `source_mt` and `source_mt_id`; a source-owner flip for the target shape between the two fixture owners; and distinct worker PIDs. Each worker selects `batch_normalization` under `scale_cancellation`.

Direct output records `source_mt=machine_learning` (`source_mt_id=15483`). The adopted receipt output records `source_mt=computer_vision` (`source_mt_id=21985`). The shape name, consequence, trigger patterns, match/name keys, donor count, and all other selected shape content agree. The changed field is used for structural Microtheory-lineage matching, so the effect reaches the shape's potential applicability metadata.

## Interpretation and next step

The receipt ordering discrepancy is now traced through three layers: edge order, name-based first-owner lookup, and active harvested shape metadata. The result still does not demonstrate an actual postulate firing difference or user-visible task change.

The next implementation direction should preserve identity through source selection: retain the selected Concept/Rule node ID with each donor, then resolve its owning Microtheory by that node ID. Keep name-level owner lookup as an explicitly multi-valued or ambiguity-reporting utility; do not let incidental edge traversal select a domain. Then validate shape and firing parity under receipt adoption, and continue the separate `graph_to_dict()` ordering-contract audit.

See [preregistration](THOUGHTEXPERIMENT_HARVEST_SHAPE_RECEIPT_LINEAGE_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_harvest_shape_receipt_lineage_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_harvest_shape_receipt_lineage_v1_raw_20261001.json).
