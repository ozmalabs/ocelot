# Fully bound edge matcher differential v3 preregistration

## Question

After correcting semi-naive driver endpoint identity, does the rebuilt matcher agree with the independent graph oracle across directed, repeated-variable, attribute-predicate, edge-type, and incremental-addition cases?

## Design

Repeat v2 with fresh seeds beginning at 202610052300. Run 32 workers over four candidate-link densities (0%, 10%, 50%, 100%) and eight replicates per density. Each worker tests four source-ordered rules: left-to-right, reverse-directed, repeated-variable self-loop, and left-to-right with a bound attribute equality predicate. Include overlapping memberships, loops in the graph population, and decoy links of another edge type. Install half the candidate relation before the first closure, then add the rest and compare all witness edge sets after the second closure. Use `add_rule_preserving_match_order` to force the edge clause position.

The independent oracle enumerates exact directed endpoint pairs and equality constraints. Distinct variables in a relation clause must map to distinct nodes; a repeated variable requires a self-edge. The v2 failed capture exposed that incremental seeding violated this invariant; v3 uses the corrected current-source build and evaluates the same outcome contract with fresh locked inputs.

## Gates

Require 32 workers, current source and native build fingerprints, exact per-rule witness digests at both closures, exact empty/complete controls, and no extra/missing witnesses after mutation. This is a targeted semantic gate, not a performance or general matcher proof.

## Limits and reproduction

This gate does not cover deletion retraction, all match/effect variants, or every scheduler route. It complements but does not replace broader engine regression coverage. Create the lock with `python3 evaluation/substrate_capability/bound_edge_matcher_differential_v3.py --lock`, run with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_bound_edge_matcher_differential_v3.py`.

