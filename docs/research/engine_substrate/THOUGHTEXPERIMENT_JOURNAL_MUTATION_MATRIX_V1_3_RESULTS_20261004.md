# Thoughtexperiment journal mutation matrix v1.3 results

V1.3 repeats the locked 17-case current-source mutation matrix and captures
the complete journal diff and whole-graph diff for each case. The checkpoint
case also captures its derived-only journal and phase interval oracle. The
post-capture divergence control stores the later whole-graph diff so that the
guarantee boundary is visible in raw data.

The independent analyzer recomputed equality from all 17 journal/oracle JSON
payload pairs. It passed all eight checks: source and lock hash agreement,
exact case set and count, journal/oracle equality, evaluator flag agreement,
phase diff equality, and explicit post-capture divergence. The direct
`node_mut` case is represented as complete before/after node attribute maps
inside the raw diffs. No timing is collected.

This improves auditability over v1.2's evaluator-emitted booleans. It remains
a finite single-threaded matrix and does not prove concurrency or higher-level
caller-path completeness. Exact global parity remains needed when arbitrary
untracked divergence is possible.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_3_PREREG_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_3.rs)
- [Locked runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_3.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_journal_mutation_matrix_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_3_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_3_20261004.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_3_analysis_20261004.json)

Run from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_3.py`.
