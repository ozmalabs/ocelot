# Grain-quantised knob step as default, v2: preregistration (2026-10-08)

Written after [v1](SUBSTRATE_KNOB_GRAIN_PROMOTION_V1_PREREG_20261008.md) and before any v2 run.

## Why there is a v2

v1's rule passed (P1–P3), but P2 passed **vacuously**: on K2 both arms scored 0, and the result exposed two pipeline defects that affect both arms.

1. **Family exclusion after one knob.** In the fixed arm, `exclude_inconclusive` (the default since tranche 10) dropped the whole `knob_edit` family after one inconclusive knob, before the builder's own per-knob exclusion could try another knob. That K2 success had come from the third attempt in tranche 7.
2. **No fallback to the next knob.** In the grain arm, the builder abstained as soon as the top-ranked knob had no separating grain step, without trying the next-ranked knob.

Fixes made before this preregistration:
- `variation_ops` v1.14.0: `knob_edit` is `retry_internal`. A trial that names a `knob_attr` carries an internal alternative, exactly like a `cue_route`.
- Grain mode walks the ranked knob candidates and abstains only if none has a separating step.

I am not promoting on a vacuous pass.

## Design

The v1 runner and arms are reused, with one corpus added:

| Corpus | Source | Note |
|---|---|---|
| K1 | as in v1 | |
| K2 | as in v1 (the tranche-7 corpus) | |
| K3 | the tranche-10 grain-probe corpus | `residual_marker_count` ∈ {0, 2, 3, 4, 5}; a regression set |

The concerns are as in v1, and K3 uses K1's two concerns. The fixes apply to both arms.

## Promotion rule (all must hold)

| Gate | Condition |
|---|---|
| Q1 | On every corpus: `grain.supported >= fixed.supported` |
| Q2 | On at least one corpus: `grain.supported > fixed.supported` |
| Q3 | `false_adoptions == 0` in every grain run |
| Q4 | No vacuous comparison: on K2 at least one arm has `supported >= 1` (otherwise K2 does not measure anything and the gate is **inconclusive**, not passed) |

If all hold, `step_mode="grain"` becomes the default, subject to the tranche regression. Otherwise it stays opt-in.

## Expectation, stated in advance

On K2 the grain step's degenerate guard may still refuse every knob, because no gate separates {0, 0.5} for "too eagerly". The fixed step's 0.5→0.6 turned reform off entirely and was judged supported in tranche 7. If so, Q1 fails on K2 and grain stays opt-in.

## Outputs

`evaluation/reports/knob_grain_promotion_v2_{K1,K2,K3}_{fixed,grain}_20261008.json` and `knob_grain_promotion_v2_20261008.json`.
