# Thoughtexperiment journal mutation matrix v1.2 results

The current-source matrix expanded from 16 to 17 cases to include direct
`TypedGraph::node_mut` writes, a public mutation surface absent from v1.1.
The source-locked dev-profile evaluator compiled and completed all 17 cases.
Every journal residual equals its whole-graph diff, including direct mutable
node access, live/fresh/tombstoned restores, node and edge writes/deletes,
repeated writes, and the checkpoint interval. The post-capture unrelated
write control is detected by the whole-graph diff and remains outside the
earlier journal receipt.

This extends finite coverage to all currently identified public semantic
mutation methods in `TypedGraph`; it does not cover arbitrary writes through
references retained across checkpoints, concurrency, every operation order,
or every caller path. The divergence control confirms global parity remains
the appropriate gate for arbitrary branch/primary equality. No performance
claim is made.

The v1.1 16-case capture remains preserved. V1.2 is a separate preregistered,
locked run after the direct-`node_mut` audit, so the extension is not a
post-capture edit. Cargo reported 48 existing crate warnings; evaluator exit
status was zero.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_2_PREREG_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_2.rs)
- [Runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_2_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_2_20261004.json)

Run from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_2.py`.
