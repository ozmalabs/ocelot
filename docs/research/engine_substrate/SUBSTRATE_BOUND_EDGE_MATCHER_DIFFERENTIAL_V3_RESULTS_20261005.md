# Fully bound edge matcher differential v3 results

## Result

The corrected native build passes all six runtime gates across 32 source-locked workers. The independent analyzer passes all nine checks, including current source/build provenance, exact seed regeneration, and independent four-rule oracle replay. All four rule shapes agree with the oracle at both closure phases for every density and replicate.

The gate confirms exact results for left-to-right directed joins, reverse-directed joins, repeated-variable self-loop clauses, and joins with a bound-attribute equality predicate. Relation density ranges from empty to complete; separate decoy edge types and overlapping left/right memberships are present. Adding the second half of candidate edges produces exactly the expected additional witnesses, with no false repeated-variable self-loops.

The v2 failed capture was diagnostically useful: the first closure passed but incremental processing created false self-loop witnesses when non-self edges were added. The cause was that semi-naive driver seeding did not enforce endpoint equality for a repeated variable. Both incremental seed sites now enforce the invariant: same variable means same node; distinct variables mean distinct nodes. The corrected v3 capture validates these four targeted shapes. Broader deletion/retraction and matcher-route coverage remain open, and this panel does not replace the full Rust suite.

## Evidence

The v2 failure and its cause are preserved in the [v2 amendment](SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V2_AMENDMENT_20261005.md), [failed capture](../../../evaluation/reports/bound_edge_matcher_differential_v2_20261005.json), and [failed analysis](../../../evaluation/reports/bound_edge_matcher_differential_v2_analysis_20261005.json). The corrected [v3 protocol](SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V3_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/bound_edge_matcher_differential_v3.py), [source lock](../../../evaluation/substrate_capability/bound_edge_matcher_differential_v3_lock_20261005.json), [capture](../../../evaluation/reports/bound_edge_matcher_differential_v3_20261005.json), and [independent analysis](../../../evaluation/reports/bound_edge_matcher_differential_v3_analysis_20261005.json) record the repaired result. Source changes are in [`substrate.rs`](../../../runners/dsl/src/substrate.rs) and [`rewrite.rs`](../../../runners/dsl/src/rewrite.rs).

