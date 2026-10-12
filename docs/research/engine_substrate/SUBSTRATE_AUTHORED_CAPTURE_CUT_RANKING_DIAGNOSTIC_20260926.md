# Authored-capture cut-ranking diagnostic protocol

**Date:** 2026-09-26. **Status:** retrospective analysis of already accepted
captures; discovery evidence only. It is not the confirmatory authored-cut
comparison preregistered in
[`SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md`](SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md).

## Question and limits

How do authored ownership, balanced native-ID groups, and a deterministic
dependency-derived ordering compare on the captured Bigville and connected
discourse graph snapshots? Use only the already captured ownership, concrete
dependency edges, trace rows, and static access declarations. No closure is
rerun; no frame is executed under a new partition; no mutation branch is
introduced. Consequently this measures cut ranking and structural sensitivity
only. It cannot establish semantic parity, useful speed, natural-task
prevalence, or fulfil the preregistered dynamic-boundary gate.

For each capture, construct an undirected simple task-node dependency graph
from the union of concrete task-to-task graph edges and observed access pairs
whose endpoints are both task nodes. Collapse repeated/directed edge instances
to one pair for partition ordering; separately report raw concrete edge counts
and observed event multiplicity. Run deterministic min-fill elimination,
breaking equal fill scores by native node ID. Make contiguous frames in that
ordering with the authored frame-size sequence in ascending authored frame
ID. The balanced-ID baseline uses the same size sequence and sorted native IDs.

Report per partition: frame sizes, task-to-task cross-frame concrete edge
count, distinct and weighted cross-frame observed access counts, fraction of
within-authored-frame node pairs retained together, distinct task nodes
incident to cross-frame edges, global-boundary edge incidence, and the
min-fill ordering's induced-width upper bound. Keep all measures distinct;
do not combine them into a completeness or quality score. Unknown/absent trace
events are not evidence of absent dependencies. If a source lacks a complete
graph-edge or rule inventory, emit the affected statistic as unavailable and
identify the captured subset; never encode missing coverage as zero.

## Frozen source captures

- Bigville: `substrate_bigville_task_access_census_v1_20260926.json` (the
  full-closure control and traced event arm from the prior task-access census).
  This capture retains the causal-influence dependency edges, not a complete
  typed graph edge inventory; global-boundary edge counts and total boundary
  node counts are therefore unavailable for this case. Its static access
  metadata records the target update rule only, not all active rules.
- Dialogue: `substrate_discourse_connected_task_census_v1_20260926.json` (the
  traced arm and its full final graph from the prior connected-task census).

The runner requires each source capture's own accepted checks to pass, records
the raw-capture digests and source-lock digests, and emits a separate lock for
this analysis. The original sources and prior failures remain untouched.

## Exclusions and next gate

This diagnostic does not implement the three boundary mutations, trace-on/off
replay for this cut comparison, partition rebuild accounting, scoped execution
or refusal, omission sensitivity, or full-graph parity under candidate cuts.
Those remain required by the confirmatory preregistration. In particular,
discourse's shared-state frame contract remains a refusal control unless a
complete mutable-global boundary update path is demonstrated. The output may
inform runner design and candidate-cut sensitivity only.
