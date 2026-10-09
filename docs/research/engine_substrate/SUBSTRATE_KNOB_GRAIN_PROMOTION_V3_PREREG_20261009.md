# Grain-quantised knob step as default, v3: preregistration (2026-10-09)

Written before any v3 run. Follows [v2](SUBSTRATE_KNOB_GRAIN_PROMOTION_V2_PREREG_20261008.md), which failed Q1 on K2.

## What changes in v3

v2 failed Q1 on K2 because the grain step's degenerate guard refused the only gate that worked there. The signal took only {0, 0.5}, and the supported fixed-step adoption (0.5 → 0.6) fires on none of the observed values.

Tranche 12 adds an opt-in **grain-end step** (`VariationOp{knob_edit}.grain_end = 1`). It is offered only when no candidate knob has an interior separating step. It moves the gate exactly one **frame quantum** past the observed frame:
- the quantum is the exact rational GCD of the gaps between distinct observed values;
- for "too eagerly" the gate moves to `max + q`, so it fires on none of the observed values;
- for "too rarely" it moves to `min`, so it fires on all of them.

The new gate lies on the frame's own lattice, so this is exact quantisation, not a tolerance. The paired-control replay still judges every result.

## Design

The arms are the v2 arms with one difference. The `grain` arm sets `step_mode="grain"` **and** `grain_end=1`; `fixed` is unchanged.

Corpora, concerns, runner logic and every other setting are as in v2: K1, K2 and K3.

## Promotion rule (unchanged from v2; all must hold)

| Gate | Condition |
|---|---|
| Q1 | `grain.supported >= fixed.supported` on every corpus |
| Q2 | `grain.supported > fixed.supported` on at least one corpus |
| Q3 | 0 false adoptions in grain |
| Q4 | K2 is not vacuous (`max(supported) >= 1`) |

If all hold, `step_mode="grain"` and `grain_end=1` become the `knob_edit` defaults in `variation_ops`, subject to the tranche regression.

## Outputs

`evaluation/reports/knob_grain_promotion_v3_*_20261009.json`. The runner refuses to overwrite.
