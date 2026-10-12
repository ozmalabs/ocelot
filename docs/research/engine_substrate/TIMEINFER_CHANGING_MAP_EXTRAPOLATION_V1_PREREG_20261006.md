# TimeInfer changing-map extrapolation v1

## Question

Does the current `TimeInfer` Term extrapolate a sequence whose per-step map
changes regularly when the changing map is linear or nonlinear, or is its
order-N trajectory support limited to rigid-translation offsets?

This is a baseline capability measurement. It makes no engine change and does
not claim that a finite fixture establishes general nonlinear induction.

## Cases

Use the existing four-cell `base_L` shape and six transitions, with stable cell
values and integer coordinates. Run each case in three fresh processes:

1. `translate_order2`: rigid translations with offsets 1, 2, 3, 4, 5, 6. This
   is the positive order-N control; the withheld next offset is 7.
2. `changing_linear_shear`: at transition k, apply `(r,c) -> (r,c+k*r)` for
   k=1..6. The withheld next transition uses k=7.
3. `changing_quadratic_shear`: at transition k, apply
   `(r,c) -> (r,c+k*r^2)` for k=1..6. The withheld next transition uses k=7.
4. `static_quadratic_shear`: apply `(r,c) -> (r,c+r^2)` at all six
   transitions. This distinguishes nonlinear-map recognition from changing
   coefficient extrapolation.
5. `random_translation`: offsets 1, 3, -2, 6, -1, 4. This is the
   incompressible-trajectory refusal control.

For each sequence, call the native `TimeInfer` Term directly and retain
`explained`, `kind`, `order`, and the predicted next frame. Independently
compare any prediction with the registered withheld next frame by exact sorted
cell equality. On a fresh graph, run the `time_axis` rules and record final
observation status and minted `latent:time` generator attributes. Direct Term
recognition, held-out exact prediction, and rule-level minting are separate
outcomes.

## Admission and interpretation gates

- Freeze this protocol, runner, analyzer, case generator, source/build inputs,
  native extension, and `time_axis` seed before running workers.
- Require exactly 15 workers, three per case, source-stable inputs, one request
  per worker, and exact paired-repeat parity for all semantic outcomes.
- The translation-order-2 control must report order 2 and predict the withheld
  frame exactly in all three workers. The random-translation control must not
  predict the withheld frame exactly or mint a time generator.
- For each map case, report recognition, order/kind, exact held-out transfer,
  and rule-level mint separately. A refusal is evidence about this current
  route and these fixtures only; any false acceptance or false mint is reported
  as a soundness failure, not averaged away.
- Report direct-Term elapsed time descriptively only. This small panel is not a
  scaling estimate and does not establish O(T), O(T^2), or any other empirical
  asymptotic law.

## Reproduction

Create the source lock using the runner's `--lock` mode, inspect it, execute the
capture, then run the independent analyzer. Preserve failed and incomplete
captures. Changes to fixtures, protocol, runner, analyzer, or source inputs
require a new version.
