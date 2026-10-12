# MetaShape multi-schema transfer panel (2026-09-26)

## Replicated result

The source-locked v1 four-schema panel failed its generalization gates. A separately locked fresh-process v1.1 replication reproduced the same per-family outcomes:

| Family | New support-2 shape | Positive holdout uses new shape | Negative fixed-field control |
|---|---|---|---|
| FrameBinding | yes | yes, `recognized` | `residual`; target refused |
| MotionRule | no; preexisting `spatial_dynamics` matched | no; `recognized_prior` via `spatial_dynamics` | `recognized_prior` via `spatial_dynamics` |
| ResourceTransfer | yes | yes, `recognized` | `recognized_prior`; `covered_by` points to new shape despite changed `status` |
| GoalTrace | yes | yes, `recognized` | `recognized_prior`; `covered_by` points to new shape despite changed `terminal` |

Across four families, 3/4 minted the expected support-2 shape, 3/4 positive holdouts used that shape, and only 1/4 negative controls remained residual and were refused by the target. All of these are counts on the locked panel, not estimates of natural prevalence or semantic error rates.

## Source-level interpretation

The two MetaShape outcomes must be kept separate. `recognized` means the higher structural decode path attributed the observation to a held signature; `recognized_prior` is the weaker last-resort `RecogniseShape` keyword-prior route. The seed's own comments describe that prior as running only after structural decode, transform decode, and dimension inference fail. The native `recognise_meta_shape` scorer scores principle keywords found in relation predicates or arguments and chooses a winner; it does not require exact agreement on the fixed field values. This explains why ResourceTransfer and GoalTrace controls with changed `status`/`terminal` values still receive a prior attribution, and why the broad preexisting `spatial_dynamics` prior absorbs MotionRule examples.

Therefore the narrow v1/v1.1 experiment-summary positive/negative pair was real but not sufficient to characterize the recognition ladder. Structural held-signature transfer worked on three minted schemas, while prior-based recognition overgeneralized on the negative controls and a preexisting prior blocked new-schema minting for MotionRule.

## Evidence

- Protocol: [v1 preregistration](SUBSTRATE_METASHAPE_MULTISCHEMA_TRANSFER_PANEL_V1_PREREG_20260926.md)
- Exact-replication amendment: [v1.1](SUBSTRATE_METASHAPE_MULTISCHEMA_TRANSFER_PANEL_V1_1_AMENDMENT_20260926.md)
- V1 [runner](../../../scripts/substrate_metashape_multischema_transfer_panel_v1.py), [lock](../../../evaluation/substrate_capability/metashape_multischema_transfer_panel_v1_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_analysis_20260926.json)
- V1.1 [runner](../../../scripts/substrate_metashape_multischema_transfer_panel_v1_1.py), [lock](../../../evaluation/substrate_capability/metashape_multischema_transfer_panel_v1_1_lock_20260926.json), [raw](../../../evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_1_20260926.json), [analysis](../../../evaluation/reports/substrate_metashape_multischema_transfer_panel_v1_1_analysis_20260926.json)
- Source: [`meta_shape_growth` rules](../../../seeds/meta_shape_growth.json), [native MetaShape recognition](../../../runners/dsl/src/shape_decode.rs)

## Next gate

Split outcome reporting by ladder rung in a larger preregistered corpus: exact structural coverage, transform/dimension coverage, keyword-prior attribution, and residual. Include adversarial same-predicate/different-fixed-value controls, held-out positive transfer, competing prior ties, and preexisting-prior controls. Measure whether a prior-attributed match improves a downstream task before treating it as accepted recognition.
