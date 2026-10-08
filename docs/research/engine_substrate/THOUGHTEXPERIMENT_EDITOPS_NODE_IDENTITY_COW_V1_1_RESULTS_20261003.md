# Thoughtexperiment node-identity CoW integration v1.1 results

## Gate result

The source-locked integration passes all 11 independent checks. Four workers
generate eight identity guard candidates and evaluate each in isolated
full-copy and shared-graph-page branches. The branch semantics match across
backends for all candidates. In every worker, only the generated actor+verb
guard passes training and the native graph-Term selector chooses it. All
selected candidates pass their held-out sequence on both backends; all-wrong
and tied selector controls abstain. The unmodified source rule also passes
training and held-outs as the positive control.

The selected training proposal is replayed on a shared-page branch. Its
mutation-journal residual changes only a preexisting `ThoughtExperimentProposal`
receipt. Revision-checked return makes the primary receipt exactly equal to the
branch receipt; a stale retry is rejected without further graph mutation. The
primary active rule store remains unchanged. This safely returns selected
proposal evidence but does not install a production repair.

## Cost

| Median worker cost | Full copy | Shared graph pages |
|---|---:|---:|
| Snapshot plus branch creation | 0.038 ms | 0.023 ms |
| Eight candidate training lifecycles | 3.18 ms | 3.08 ms |
| Eight candidate held-out lifecycles | 3.20 ms | 2.98 ms |
| Receipt graph-delta adoption | — | 0.139 ms |

The measured lifecycles include branch rule replacement, input materialization,
and closure. Both backends perform similarly on this small graph; this is not a
scaling or economic advantage claim. The CoW mechanism gives isolation and a
clean branch contract at little measured fork cost here.

## Limits and next gate

The task, target, fault, examples, and expected outcome are supplied by the
harness, and the test covers one actor/verb family. Candidate trials use
isolated branches, but the returned receipt remains a pending proposal and the
primary rule store is deliberately unchanged. The v1 capture is retained as a
diagnostic because its post-capture analyzer used the wrong timing-field name;
v1.1 reruns the same design with the corrected analyzer included in its lock.
Do not count v1 as a separate replication.

The next gate is a multi-family run pairing actor identity with recurrence and
conversation, then an explicit approval/adoption path for selected rule changes
that preserves atomicity with graph residuals. Candidate target diagnosis and
task-level self-improvement benefit remain unmeasured.

## Artifacts

- [V1.1 protocol](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1.py) and [analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_editops_node_identity_cow_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1_lock_20261003.json)
- [Training orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_orders_20261003.json), [held-out scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_scores_20261003.json), and [analysis](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_analysis_20261003.json)
- V1 diagnostic artifacts: [protocol](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_PREREG_20261003.md), [source lock](../../../evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_lock_20261003.json), [orders](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_orders_20261003.json), and [scores](../../../evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_scores_20261003.json)
