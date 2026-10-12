# Thoughtexperiment journal mutation matrix v1.6 results

The preregistered 26-case current-source evaluator passed, with every journal
residual equal to an independent diff of the branch's underlying graph state.
The independent analyzer passed its full case-set, source-lock, revision,
checkpoint, divergence, aperture, and payload checks. A fresh static audit also
passed for the 23 public mutable `TypedGraph` methods against the updated source.

The new cases cover replacement of a hidden pre-existing edge, deletion by a
retained hidden edge identity, batch deletion of hidden edges, deletion of a
visible edge in a narrow scope, and insertion under a narrow scope. The first
three now produce exact before-images: replacement is represented as an edge
change, and deletion as an edge removal. This required two source corrections:
edge replacement now finds the underlying edge when the scoped lookup misses;
single and batch deletion record actual prior attributes even when the edge is
hidden from reads. The narrow aperture remains a read restriction, not mutation
authorization. The tested sequences are direct and single-threaded; arbitrary
scope/write interleavings, concurrency, and performance remain outside scope.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_6_PREREG_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_6.rs)
- [Locked runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_6.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_6.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_6_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_6_20261004.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_6_analysis_20261004.json)
- [Current-source mutation audit](../../../evaluation/reports/thoughtexperiment_tracked_mutations_v2_20261004.json)

Run the matrix from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_6.py`.
Run the source audit with
`python3 evaluation/substrate_capability/audit_thoughtexperiment_tracked_mutations_v2.py`.
