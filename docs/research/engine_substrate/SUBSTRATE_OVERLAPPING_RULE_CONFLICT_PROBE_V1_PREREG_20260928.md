# Overlapping rule conflict and cycle probe v1

## Question

When two rules with the same match and same true predicate write different values to the same attribute, does the substrate reach a fixed point, and how do insertion order, progress budget, and cycle detection affect the reported outcome?

## Design

- Three independent workers; each builds four fresh one-binding fixtures: rule orders A→B and B→A, each under cycle detection off/on.
- Both rules use the same stable callback predicate and `set_attr_if_different(accepted, value)`, with A writing `1` and B writing `2`.
- Run through `run_rules_report(max_steps=12, detect_cycles=...)`. Capture status, pass/progress counts, callback count, and final graph value.
- Source/native code and callback fixture are locked before workers.

## Gates

All workers complete all four cells with stable locks and replicate the same result per cell. Cycle detection must distinguish a repeated graph state from fixed point. The bounded non-cycle arm must expose the budget termination. The resulting value is reported by insertion order; no order-invariance expectation is imposed because the rules have deliberately conflicting effects.

## Claim limits

One binding and one conflicting attribute. This tests deterministic conflict and termination handling, not arbitrary critical-pair coverage or compensation confluence. A repeated state is evidence of a cycle in this fixture; the generic detector fingerprints graph state and may not represent every external dependency or pending side channel.
