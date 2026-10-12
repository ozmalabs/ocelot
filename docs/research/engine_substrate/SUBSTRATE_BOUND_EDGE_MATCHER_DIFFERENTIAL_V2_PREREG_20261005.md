# Fully bound edge matcher differential v2 preregistration

## Question

Does the direct edge-membership matcher preserve results across multiple bound endpoint shapes, including a repeated variable and a where predicate, under directed relation updates and edge-type decoys?

## Design

Run 32 fresh workers: four candidate-link densities (0%, 10%, 50%, 100%) × eight deterministic seeds. Each worker constructs one small graph with overlapping left/right item memberships, per-item bucket attributes, directed candidate links that may include self-loops, and decoy links under a second relation type. Install four source-ordered rules using `add_rule_preserving_match_order`:

1. left-to-right candidate edge;
2. reverse-directed candidate edge;
3. a repeated-variable self-loop clause after binding that item;
4. left-to-right candidate edge plus a bound-attribute equality predicate.

Install half the selected candidate links, run closure, add the remainder, and run again. At both points compare each witness edge set with an independent oracle that checks direction, edge type, endpoint memberships, the repeated-variable case, and the bucket predicate. Every rule uses its witness edge type as a separate output so one route cannot mask another.

## Gates

Require 32 successful source-locked workers, stable source hashes, exact first/final witness digests for all four rule shapes, correct empty/complete controls, and exact incremental additions. Analyze panel construction independently from captured outputs. This is a semantic gate; timing is recorded only for diagnostics.

## Limits

This broadens targeted semantics for the changed both-bound path but does not cover deletion retraction or every rule/effect variant. The engine's closure is insertion-oriented; deleting a premise does not imply automatic retraction of previously derived facts, so deletion behavior is not treated as a positive closure oracle here. This does not replace the full Rust suite or constitute a proof of matcher correctness.

## Reproduction

Create the lock with `python3 evaluation/substrate_capability/bound_edge_matcher_differential_v2.py --lock`, run with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_bound_edge_matcher_differential_v2.py`.

