# Harvest-shape owner-collision exposure v1 results

**Result:** one of the 14 currently selected implication shapes uses a multiply-owned source name, so owner ordering reaches active harvested metadata.

## Capture

Three fresh full-boot workers pass all gates with stable fingerprints and deterministic shape/collision output. Each loads 731 seeds with 11 failures, sees 224 ambiguous named owner groups, and selects the same 14 shapes. Exactly one selected shape source intersects a multi-owner name: `scale_cancellation` is sourced from `batch_normalization`, whose owners are `machine_learning` (node 15483) and `computer_vision` (node 21985). The current order resolves its `source_mt` metadata to `machine_learning`.

## Interpretation

This moves the issue from a helper-only possibility to an active shape-metadata exposure. The shape's `source_mt` and `source_mt_id` are used for structural Microtheory-lineage applicability, so a changed attribution can affect where `scale_cancellation` is eligible to fire. The exposure panel itself did not perturb edge order or compare downstream behavior; it does not show a receipt-induced shape change yet.

Next run both `harvest_shapes()` and downstream applicability against Direct and receipt-adopted states after a controlled rewrite of the two corpus-derived `batch_normalization` ownership rows. Preserve all shape content and canonical graph facts, then determine whether source lineage or firing outcomes differ.

See [preregistration](THOUGHTEXPERIMENT_HARVEST_SHAPE_OWNER_COLLISION_V1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_harvest_shape_owner_collision_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_harvest_shape_owner_collision_v1_raw_20261001.json).
