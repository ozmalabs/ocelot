# Runtime CAN match-order sensitivity v1.1 held-out preregistration (2026-09-29)

## Question

Does the sparse-first Hebbian join-order result replicate on held-out deterministic factor draws after the original reps 0/1?

## Design

Repeat the same baseline versus in-memory sparse-first pattern-order comparison using rep indices 2 and 3, at N=128/256, path/banded2, and both state vocabularies (16 fresh workers). Each worker runs baseline and reordered closure uninstrumented, then runs separate audit-enabled baseline and reordered twins for per-rule candidate/Term counts. Counterbalance both execution orders by replicate. The held-out factor seeds are derived from the unchanged fixture seed formula with rep=2/3; no protocol thresholds or cases depend on interim results.

Compare full canonical graph signatures, extracted CAN model, progress counts, independent fixed-point residual, terminal no-work probe, and source locks. Report uninstrumented times and instrumented counters separately. This is an out-of-sample replicate of the same CAN rule family and topology cells; the second authored family has its own separate current-source replay artifact.

## Integrity gates

Require 16 unique PIDs and exact held-out cell coverage; exact source/native lock equality before, during, and after; exactly two match-order permutations; baseline/reordered semantic parity; audited/unaudited parity per arm; zero residuals and terminal work; and complete target-rule counter capture. Report all outcomes.

## Scope

Held-out deterministic fixture draws only; no natural task sampling and no production seed edit. This tests transfer across factors/seeds, not across CAN rule definitions.

## Reproduction

```sh
python3 evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_1.py --lock
python3 evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_1.py
```
