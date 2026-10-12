# Thoughtexperiment journal mutation matrix v1.4 results

The source-locked evaluator completed 20 fixed mutation cases. All 20 journal
residuals matched independently computed whole-graph diffs at capture, including
identity-preserving edge restoration and the checkpointed phase interval. The
post-capture divergence control also behaved as expected: a later tracked write
advanced the revision and made the earlier journal differ from the global diff.
The independent analyzer passed source/lock, case-set, payload equality,
revision expectation, scope transition, derived-index, and divergence checks.

The scope transition used all fixture nodes so the aperture changed without
hiding any fixture edge. It advanced the mutation revision and had an empty
semantic graph diff. The derived-index declaration advanced neither revision
nor semantic diff. These controls confirm the intended distinction for these
specific calls. They do not establish journal parity when an aperture hides
existing edges; which motivated v1.5. The follow-up shows this was an oracle mismatch: a scoped serialization is an observation projection, and hidden edges are not semantic deletions. See the v1.5 report for the corrected full-state oracle. The matrix remains finite and single-threaded, and says nothing about concurrent execution, arbitrary caller paths, or performance.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_4_PREREG_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_4.rs)
- [Locked runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_4.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_4.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_4_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_4_20261004.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_4_analysis_20261004.json)

Run from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_4.py`.
