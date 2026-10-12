# Thoughtexperiment journal mutation matrix v1.1 results

## Result

The locked current-source evaluator compiled and completed all 16 registered
cases. Every journal delta matched the corresponding whole-graph diff,
including node and edge attributes, node type changes, additions, removals,
edge replacement, duplicate indices in batch deletion, repeated writes, live
identity replacement, and restoration of fresh and tombstoned IDs. The
post-checkpoint `derived_only` journal matched a full graph diff of the
post-checkpoint interval. The post-capture divergence control also behaved
as intended: the earlier journaled residual did not include the later write
to another node, while a new whole-graph diff did.

| Gate | Result |
|---|---:|
| Registered mutation cases | 16 / 16 |
| Journal/full-diff equality at capture | 16 / 16 |
| Phase journal/full-diff equality | 16 / 16 (applicable checkpoint case passes; other rows have no phase interval) |
| Deliberate post-capture divergence detected by full diff | pass |

## Interpretation

The earlier `restore_node` defect is corrected: a live ID replacement now
retains the prior node record in the journal, and the live-restoration case
matches the exact full-graph oracle. Fresh and tombstoned restoration also
match. This supports journal coverage for the enumerated `TypedGraph`
mutation methods and fixed operation sequences.

The control confirms the guarantee boundary. A journal can match the branch
at capture time and still fail to describe later, unrelated, or otherwise
untracked changes. Therefore this result does not justify removing exact
branch/primary graph parity checks where arbitrary divergence must be
excluded. It does not cover concurrent writes, hidden mutation routes outside
the enumerated API, or every operation ordering and value shape. There is no
timing or general tractability claim.

The initial exploratory run is excluded because it did not follow the
release-profile argv in the original lock. The confirmatory v1.1 amendment
locked the dev-profile command before rerunning. Cargo reported 48 existing
crate warnings; the evaluator completed successfully.

## Reproduction artifacts

- [Protocol](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_PREREG_20261004.md)
- [Execution amendment](THOUGHTEXPERIMENT_JOURNAL_MUTATION_MATRIX_V1_1_AMENDMENT_20261004.md)
- [Evaluator source](../../../runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1.rs)
- [Locked runner](../../../evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_journal_mutation_matrix_v1_1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_journal_mutation_matrix_v1_1_20261004.json)

Run from the repository root with
`python3 evaluation/substrate_capability/run_thoughtexperiment_journal_mutation_matrix_v1_1.py`.
