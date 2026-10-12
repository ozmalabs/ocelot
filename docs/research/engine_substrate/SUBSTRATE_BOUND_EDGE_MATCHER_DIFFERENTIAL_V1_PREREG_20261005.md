# Fully bound edge matcher differential v1 preregistration

## Question

Does the direct `has_edge` path for fully bound match clauses preserve the exact relation semantics and monotonic mutation behavior of the previous neighbor-enumeration matcher?

## Design

Run 32 fresh native workers: four directed relation densities (0%, 10%, 50%, 100%) and eight deterministic seeds per density. Each graph has overlapping left/right membership sets so that repeated-node pairs are possible, directed `rel_a` edges under test, and `rel_b` decoy edges on overlapping endpoint pairs. A source-ordered three-edge rule first binds `episode`, left item, and right item, then tests the fully bound `rel_a` edge and emits a `witness` edge. Use `add_rule_preserving_match_order` so the target clause is known to execute after both endpoints bind.

For each worker, run once with a deterministic half of its selected `rel_a` edges installed; then add the remaining selected `rel_a` edges and run to closure again. At both phases compare witness edge identity against an independent directed graph oracle. The oracle excludes same-node pairs because the rule matcher requires distinct nodes for distinct variables. The decoy edge type must never produce a witness. Record graph size, relation and witness digests, parity, closure time, and source provenance.

## Gates

Require 32 successful source-locked workers, stable source fingerprints, exact oracle parity at both phases, exact directed edge-type behavior, empty/complete controls, and correct incremental witness additions after graph mutation. Analyze results independently from the locked seed/panel descriptions. Timings are descriptive only; this gate is for semantic coverage.

## Limits

This is targeted differential coverage of the fully bound edge clause and add-only graph mutation. It does not replace the general Rust suite, establish all matcher invariants, or measure natural-task capability. It deliberately keeps each worker small so that every relation pair can be independently enumerated.

## Reproduction

Create the immutable lock with `python3 evaluation/substrate_capability/bound_edge_matcher_differential_v1.py --lock`, run with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_bound_edge_matcher_differential_v1.py`.

