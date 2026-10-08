# Adequacy probe selection under a fixed budget v1.1 — amended preregistration

## Amendment

The v1 capture is retained as diagnostic. Its singleton domain contained both acquisition inputs, so the worker removed every domain point as non-fresh and accepted without making a label request. The case did not measure the registered singleton fresh alias. V1.1 replaces it with disjoint acquisition `{x=0}` and a deliberately sparse domain: `x=1..31` are aliases and `x=32` distinguishes the models. The v1 capture is not used as confirmatory evidence.

## Question and cases

At equal label budgets, does target-blind maximum prediction entropy over a candidate and caller-supplied alternatives reduce false acceptance relative to seeded hash sampling? Does this depend on the target being represented in the alternatives and on a distinguishing input existing in the finite domain?

Use a degree-31 product `D(x)=∏(x−i)` for `i=1..31`. The candidate is `x`. The cases are:

| Case | Hidden target | Candidate | Supplied alternative(s) | Fresh domain |
|---|---|---|---|---|
| represented wrong | `x + D(x)` | `x` | `x + D(x)` | `1..32` |
| correct adoption | `x + D(x)` | `x + D(x)` | `x` | `1..32` |
| omitted target | `x + 2D(x)` | `x` | `x + D(x)` | `1..32` |
| finite alias | `x + 2D(x)` | `x` | `x + D(x)` | `1..31` |

All rows agree with the candidate at acquisition input `x=0`; the first three cases have exactly one distinguishing fresh point (`x=32`). In the final case every admissible fresh input aliases. The target label is withheld until selection and is computed by an independent integer oracle in the runner.

## Policies, budget, and measures

Compare seeded hash sampling against greedy maximum Shannon entropy over native predictions for the candidate plus currently label-consistent alternatives. Ties use the same seeded hash order. Reveal one analytic label after each choice and remove inconsistent alternatives. Use nested prefix budgets 1, 2, and 4 and 30 deterministic repetitions per case. Measure selected inputs, native evaluation/selection cost, label count, candidate acceptance, and exactness on sealed integer held-outs. Report false acceptance for wrong candidates, useful acceptance for the correct candidate, and label cost independently.

## Limits

This is an adversarial finite scalar benchmark with a caller-provided alternative set and harness-authored labels. The maximum-entropy policy can find a witness only if its domain contains one and its supplied alternatives expose disagreement there; it cannot validate an omitted model over an alias-only domain. This study measures a selector strategy, not production integration, general adequacy, trusted-provider identity, or natural-task rates.
