# Thoughtexperiment journal mutation matrix v1.3 preregistration

Date: 2026-10-04

## Objective

Repeat the 17-case current-source journal coverage matrix while preserving
enough raw semantic output for an independent analyzer to recompute each
journal/oracle comparison.

## Method and locked inputs

The evaluator executes the fixed mutation sequences documented in the v1.2
preregistration: direct `node_mut`; node setters; live, fresh, and tombstoned
restore; node deletion/insertion; edge insertion, replacement, attribute
mutation, single/batch deletion; repeated writes; phase checkpoint; and the
post-capture divergence control. It records, per case, the complete JSON
journal delta and whole-graph diff. The checkpoint case also records both
derived-only payloads; the divergence control records a second whole-graph
diff after the untracked write.

Before compilation or execution, lock this protocol, evaluator source,
capture runner, independent analyzer, graph/persistence/value/interner
sources, Cargo manifest, and lockfile. Run the dev-profile Cargo command
through the locked capture runner. Then run the independently implemented
Python analyzer against the raw payloads; the analyzer checks lock hashes,
case identity/count, recomputed structural equality, phase equality, and the
expected divergence. Require all 17 case diffs to match and all analysis
checks to pass. No timing is collected.

## Claim limits

This is a finite, single-threaded method matrix over fixed values and
operation orders. It does not establish concurrency safety, retained-reference
behavior beyond Rust's borrowing constraints, completeness of all higher
level caller paths, or equality after arbitrary untracked writes. No
performance or broad tractability claim follows.
