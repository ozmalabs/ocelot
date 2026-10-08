# Thoughtexperiment generated-residual adoption v1.1 — results

**Date:** 2026-10-01  
**Status:** all 72 source-locked trials pass all semantic and isolation gates.

Three fresh workers each ran the preregistered four-family × two-size × three-seed panel. The families exercise node-attribute mutation, node/edge addition, the earlier mixed add/change/delete combination, and deletion of a degree-32 hub. Graphs contain 64 or 1,000 semantic nodes; context edges are seeded and outside the target aperture except for hub spokes.

Every trial executes a real graph-resident rule through `imagine()`, regrounding, the default refusal gate, and explicitly approved writeback. All rehearsals and refusals preserve the complete primary semantic graph. Expected rule conclusions and final write effects match their family-specific sets; hub incident-edge removals are correctly represented as cascade write effects rather than independent rule conclusions. Every approved result matches an independent full-graph oracle exactly.

## Median phase times (ms)

| Family / nodes | `imagine` total | Snapshot/setup | Residual readout | Reground | Refusal gate | Approved commit |
|---|---:|---:|---:|---:|---:|---:|
| attribute / 64 | 1.43 | 0.31 | 0.25 | 0.29 | 0.19 | 22.19 |
| attribute / 1,000 | 2.56 | 0.98 | 0.24 | 0.29 | 0.13 | 60.48 |
| add / 64 | 4.43 | 0.34 | 1.08 | 0.96 | 0.51 | 20.50 |
| add / 1,000 | 4.67 | 1.07 | 0.75 | 0.71 | 0.47 | 56.25 |
| mixed / 64 | 2.73 | 0.37 | 0.53 | 0.51 | 0.30 | 19.03 |
| mixed / 1,000 | 4.54 | 1.38 | 0.65 | 0.62 | 0.28 | 58.14 |
| hub delete / 64 | 6.61 | 0.35 | 2.21 | 0.54 | 0.51 | 18.30 |
| hub delete / 1,000 | 5.10 | 0.59 | 1.80 | 0.35 | 0.65 | 30.85 |

These are pooled medians over nine trials per cell on one host, not stable service-level estimates. The larger graph raises snapshot/setup cost for attribute, add, and mixed cases, consistent with their `2 × nodes` background-edge construction; hub-delete snapshot timing is non-monotonic and needs more repeats. Hub deletion has the largest residual-readout cost within each size in this panel, as expected from its wider aperture. Approved commit is far more expensive than refusal or regrounding, but this panel does not isolate which commit subphase dominates. No asymptotic or natural-task claim follows.

This advances the earlier one-rule result by showing exact adoption over multiple generated effect families and a wider deletion aperture at two fixture sizes. It still does not test rule learning, natural-task prevalence or utility, conflict under concurrent writers, nor an empirical distribution of frame boundaries. Next use held-out task-generated rules/receipts and independently vary node count, background-edge density, and hub degree while capturing commit subphases.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_GENERATED_RESIDUAL_ADOPTION_V1_1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_generated_residual_adoption_v1_1.py)
- [Raw three-worker capture](../../../evaluation/reports/thoughtexperiment_generated_residual_adoption_v1_1.json)
