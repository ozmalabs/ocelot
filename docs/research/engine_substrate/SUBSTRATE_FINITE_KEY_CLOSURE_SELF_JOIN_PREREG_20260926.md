# Finite-key closure self-join gate — preregistration (2026-09-26)

**Status:** confirmatory for the generated repeated-variable schemas below. Extends the restricted closure evidence to analyzer-accepted equality constraints and negative controls; not a general parser-completeness claim.

## Frozen design

Three fixed rules, installed in three orders (`LRT`, `TRL`, `RLT`):

- L: positive repeated-variable self-loop match `loop(x,x)`; mint/reuse `Witness{tag:"L"}`; add `has_loop(x,L)`.
- R: positive reciprocal two-edge join `rel(x,y) ∧ rel(y,x)`; mint/reuse `Witness{tag:"R"}`; add `has_recip(x,R)`.
- T: positive three-edge cycle join `rel(x,y) ∧ rel(y,z) ∧ rel(z,x)`; mint/reuse `Witness{tag:"T"}`; add `has_tri(x,T)`.

Initial graph strata:

- `rich_triangles`: N ∈ {3,6,9}; self-loop on every node; disjoint 3-cycles in both directions on `rel` (activates L, R, T).
- `self_only`: N ∈ {3,6,9}; self-loop on every node and no `rel` edges (activates L only; R/T null controls).
- `reciprocal_pairs`: N ∈ {4,6}; no `loop`; disjoint reciprocal `rel` pairs (activates R only; L/T null controls).

Three independently constructed substrates per stratum × rule order; 72 cases. Fixed closure budget 200,000, cycle detection off. One interpreter replays positive joins by variable unification and evaluates insertion effects to fixed point; it is separate from the native matcher/scheduler.

## Gates

Static analyzer must accept the exact repeated-variable rule specs and compute M=3 syntactic literal signatures, E=5 edge types, and `B=M+E(N+M)^2−e₀`. Native closure must reach fixed point, match the independent terminal graph exactly, and remain within B. Terminal semantics must be identical across rule orders. Null controls must not invent witnesses for unsatisfied rules: self_only yields only L; reciprocal_pairs yields only R; rich_triangles yields all three.

Preserve all initial/final graphs, run reports, rule specs, analyzer outputs, and provenance hashes. This design measures semantic behavior, not latency. Unsupported effects, negation, mutation, deletion, computed mint values, or external state remain excluded.

## Command

```sh
PYTHONPATH=.:runners/dsl/python python3 scripts/verify_mint_termination_self_join_v1.py
python3 scripts/analyze_mint_termination_self_join_v1.py
```
