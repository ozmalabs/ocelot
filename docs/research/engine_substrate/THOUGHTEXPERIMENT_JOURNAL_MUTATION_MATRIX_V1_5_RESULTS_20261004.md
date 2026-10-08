# Thoughtexperiment journal mutation matrix v1.5 results

The source-locked 21-case evaluator passed. Its independent analyzer recomputed
all journal/full-state diff equalities and passed every integrity and semantic
check, including revision expectations, the checkpoint interval, the deliberate
post-capture divergence control, and the new narrow-scope case.

In the narrow-scope case, the branch hides two fixture edges, then performs a
tracked node-attribute write. Serialization while the aperture is active
reports both hidden edges as removed. After the journal is finished, clearing
the read restriction exposes the branch's underlying graph, whose full-state
diff matches the journal: only the node attribute changed. Thus the journal is
a semantic residual; the scoped serialization is a read projection. Consumers
must not apply view-only omissions as primary graph deletions. This resolves the
v1.4 oracle ambiguity for the tested sequence, but does not cover arbitrary
interleavings of scope changes and edge mutations.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_5_PREREG_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_5.rs)
- [Locked runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_5.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_5.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_5_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_5_20261004.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_5_analysis_20261004.json)

Run from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_5.py`.
