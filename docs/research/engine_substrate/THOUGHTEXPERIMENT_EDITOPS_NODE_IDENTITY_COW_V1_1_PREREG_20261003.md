# Thoughtexperiment node-identity CoW integration v1.1 preregistration

V1's order and score captures were written under a runner/analyzer lock, but
the post-capture analyzer referenced `patch_ns` while the runner records
`rule_patch_ns`; analysis stopped before output. V1 artifacts remain
diagnostic. V1.1 changes artifact identities and fixes the analyzer field name;
it reruns the same frozen four-worker panel under a new pre-capture lock.

The experiment tests generated actor/verb identity hypotheses inside isolated
full-copy and shared-graph-page snapshot branches. Four workers each freeze
candidate order, score all eight edge/attribute guards on the same training
sequence, and pass opaque candidate IDs plus outcomes to the native graph-Term
selector. The held-out stage scores all candidates under both backends after
selection. The selected training hypothesis is replayed on a shared-page
branch; only its `ThoughtExperimentProposal` receipt update is returned through
the revision-checked graph-delta API. The primary rule remains unmodified. A
stale residual retry must be rejected without graph mutation.

The fixed input sequences and gate thresholds are otherwise identical to
[v1](THOUGHTEXPERIMENT_EDITOPS_NODE_IDENTITY_COW_V1_PREREG_20261003.md). The
v1.1 lock includes the corrected analyzer, runner, actor task path, shared
generator, and native build. This is a confirmatory rerun of the same
synthetic task, not an independent task-family replication.
