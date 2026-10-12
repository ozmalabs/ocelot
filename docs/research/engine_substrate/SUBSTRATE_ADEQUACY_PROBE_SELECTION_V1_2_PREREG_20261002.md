# Adequacy probe selection under a fixed budget v1.2 — amended preregistration

## Amendment

The v1.1 capture is retained as diagnostic only. Its degree-31 product exceeded the native signed-integer range; native Term evaluation wrapped while the independent integer oracle did not. V1.2 uses twelve roots, so the sole witness at `x=13` is `12!`, within signed 64-bit range, and all sealed held-outs through `x=17` also remain in range. The registered source now locks this reduced design. No v1 or v1.1 capture is confirmatory evidence.

## Question and cases

At equal label budgets, does target-blind maximum prediction entropy over a candidate and caller-supplied alternatives reduce false acceptance relative to seeded hash sampling? Does performance depend on the target appearing in the alternative set and a distinguishing input existing in the declared domain?

Define `D(x)=∏(x−i)` for `i=1..12`. At acquisition `x=0`, all models below return zero. Inputs `x=1..12` alias; `x=13` is the only fresh witness in the broad domain.

| Case | Hidden target | Candidate | Supplied alternatives | Fresh domain |
|---|---|---|---|---|
| represented wrong | `x + D(x)` | `x` | `x + D(x)` | `1..13` |
| correct adoption | `x + D(x)` | `x + D(x)` | `x` | `1..13` |
| omitted target | `x + 2D(x)` | `x` | `x + D(x)` | `1..13` |
| finite alias | `x + 2D(x)` | `x` | `x + D(x)` | `1..12` |

The target label is hidden until probe choice and comes from an integer expression in the runner. Native Term evaluation supplies all candidate/challenger predictions.

## Policies, budget, and measures

Compare seeded hash sampling with greedy maximum Shannon entropy over native predictions for the candidate and currently label-consistent alternatives. Ties use the seeded hash order. Reveal one analytic label after each choice, then remove inconsistent alternatives. Use nested prefix budgets 1, 2, and 4, with 30 deterministic repetitions per case. Record selected inputs, native evaluation/selection cost, label count, candidate acceptance, and exactness on sealed held-outs. Report false acceptance, useful acceptance, false refusal, and label cost separately.

## Limits

This is an adversarial finite scalar benchmark with caller-supplied alternatives and harness-authored labels. The selector can expose a witness only when the domain contains one and its alternatives disagree there. It cannot validate an omitted target over an alias-only domain. The result measures a selection strategy, not production integration, trusted-provider identity, general adequacy, or natural-task rates.
