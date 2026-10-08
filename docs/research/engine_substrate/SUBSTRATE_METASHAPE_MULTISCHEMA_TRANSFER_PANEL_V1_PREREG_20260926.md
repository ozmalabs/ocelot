# MetaShape multi-schema transfer panel v1 preregistration (2026-09-26)

## Question

Does the same recurrence-based MetaShape learner acquire and transfer a held-out relation abstraction across several previously unseen item types, while rejecting a control that changes a fixed field?

## Fixed panel

All items use the ordinary `domains.teach.teach` → `meta_shape.observe` route with a temporary seed directory and `OZMA_SEED_PERSIST_DISABLED=1`. Load only the `meta_shape_growth` dependency closure. For each family, submit two training items varying `variable_a`/`variable_b` while holding the named fixed field constant, then one positive holdout with new variable values and the same fixed value, then one negative control with new variable values and a changed fixed value.

| Item type | Fixed field | Training values | Positive holdout | Negative control |
|---|---|---|---|---|
| `FrameBindingProbe` | `count=7` | `role/source`, `interface/north`; `role/target`, `interface/south` | `role/relay`, `interface/east`, `count=7` | same variables, `count=9` |
| `MotionRuleProbe` | `order=1` | `mode/translate`, `axis/x`; `mode/reflect`, `axis/y` | `mode/rotate`, `axis/z`, `order=1` | same variables, `order=2` |
| `ResourceTransferProbe` | `status=complete` | `source/r1`, `target/r2`; `source/r3`, `target/r4` | `source/r5`, `target/r6`, `status=complete` | same variables, `status=failed` |
| `GoalTraceProbe` | `terminal=false` | `phase/analysis`, `channel/symbolic`; `phase/planning`, `channel/embodied` | `phase/acting`, `channel/external`, `terminal=false` | same variables, `terminal=true` |

Submit all four training pairs first, then all positive holdouts, then all negative controls. Preserve this order. Record every observation status, `covered_by`, residual, each newly minted MetaShape signature/support, seed/source hashes, and persistence state.

## Primary gates

- Two-seed dependency closure loads without failure and real seed persistence remains disabled.
- Each family mints exactly one support-2 shape after its pair.
- All four positive holdouts are recognized and attributed to the family-specific minted shape.
- All four negative controls are not attributed to that shape and remain residual.
- No extra MetaShape is minted by any held-out item.
- The source/input lock matches the capture.

This is a 4-schema / 4-positive / 4-negative authored panel. It measures schema-conditioned transfer and fixed-relation sensitivity only; it does not estimate natural prevalence, broad false-positive rate, semantic validity, or task utility.
