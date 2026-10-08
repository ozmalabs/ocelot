# Finite-key closure rule-interaction gate — preregistration (2026-09-26)

**Status:** confirmatory for the generated finite-key rule family below; not a general proof for every analyzer-admitted program. This specifically expands rule-body shape, edge-type diversity, and rule ordering after the N≤64 one-schema scale gate.

## Frozen matrix

- Initial nodes: N ∈ {4,8} with `idx` attributes.
- Initial topologies: directed cycle and directed path, each represented independently in both `link` and `rel` edge types.
- Three mutually interacting rules, installed in each of three orders: ABC, CBA, BCA.
  - A: one positive `link(x,y)` match; mint/reuse `Witness{tag:"A"}`; add `made_a(x,A)`.
  - B: two-positive-edge match `link(x,y) ∧ rel(y,z)`; mint/reuse `Witness{tag:"B"}`; add `made_b(x,B)`.
  - C: two-positive-edge match `made_a(x,a) ∧ made_b(x,b)`; mint/reuse `Witness{tag:"C"}`; add `result(a,C)` and `result(b,C)`.
- Three fresh native substrate constructions per N×topology×order cell; 36 cases total; fixed closure budget 200,000; no cycle detector.
- Analyzer receives the full initial node/edge inventory and each exact rule spec. Expected M=3 literal mint signatures and E=5 edge types (`link`,`rel`,`made_a`,`made_b`,`result`).

## Primary checks

1. Static analyzer accepts every specified rule program and returns `B=M+E(N+M)^2−e₀`.
2. A separate monotone rule interpreter, independent of the native scheduler, reaches a stable graph for the exact same rule program and initial graph.
3. Native loader/scheduler reaches `fixed_point`, not budget exit; normalized node attributes and exact typed/attributed edge set equal the reference closure.
4. Native progress steps remain ≤B; all three rule orders yield the same terminal semantic graph per N/topology.
5. Record all per-case graphs, match/rule specs, status, passes, progress, bound, and provenance hashes. No latency claim is primary.

## Failure handling and boundary

Retain every cell. A semantic mismatch, refusal, budget exit, nontermination, analyzer rejection, or order-dependent final state fails the gate and must be explained before any amendment. This does not cover negation, attribute mutation, deletion, computed mint values, external state, dynamic rule patches, variable-arity scaling, or every accepted parser form. No result generalizes beyond this generated program family.

## Commands

```sh
PYTHONPATH=.:runners/dsl/python python3 scripts/verify_mint_termination_interaction_v1.py
python3 scripts/analyze_mint_termination_interaction_v1.py
```
