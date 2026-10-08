# Runtime CAN match-order sensitivity v1 preregistration (2026-09-29)

## Question

Can the current CAN rule match clauses enumerate sparse coactivation links before the quadratic `mt→Concept` membership join, reducing candidate/Term work while preserving the complete settled graph and concept state?

## Design

Compare the locked baseline seed with an in-memory variant that changes only the `match` clause order for `can_native_hebbian_mint` and `can_native_hebbian_reweight`. For each, move `a coactivated_with coact` and `coact coactivation_of b` before the two `mt has_concept` clauses. This is a conjunction-preserving join order; no pattern, where condition, effect, or seed file is changed. Use N=128/256, path/banded2, 2-/3-state, and two deterministic replicates (16 fresh workers).

Each worker runs both variants uninstrumented for closure timing and runs a fresh audit-enabled variant for per-rule counters. Counterbalance which uninstrumented variant runs first by replicate parity. A canonical whole-graph signature ignores native allocation IDs but includes node types/attributes and typed directed edges; also compare progress, named Concept attributes, extracted CAN factors, and an independent fixed-point residual. Compare candidate-pair and Term-evaluation counters to the same-cell baseline in the preceding locked closure-attribution capture.

## Integrity and adoption gates

Require 16 unique PIDs and full cell coverage; unchanged source/seed/native lock; exactly two match-array permutations in the variant; uninstrumented baseline/variant canonical graph, Concept state, progress, and extracted factors equal; audited variant parity with its uninstrumented twin; zero independent residuals/terminal work; complete baseline and variant counters. Report counters even if they do not fall. A reduction is not considered useful if state/graph parity fails or instrumentation-off timing regresses consistently. Any eventual seed change requires a separate explicit implementation change; this experiment changes only an in-memory benchmark copy.

## Scope

This probes one authored CAN seed, two sparse topologies, and one join-order change. It is not a generic optimizer benchmark, does not prove confluence, and does not estimate natural workloads.

## Reproduction

```sh
python3 evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1.py --lock
python3 evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1.py
```
