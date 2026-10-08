# Protocol: predecessor-dependent closure in CoW thought experiments

Date: 2026-10-03

Status: protocol written before capture; source lock records the executed implementation.

## Research question

Can the substrate execute predecessor-dependent communication rules inside an
isolated thought-experiment branch, preserve the primary until approval, and
return an exact graph residual whose application reproduces the branch's
result? Does scoped closure preserve the same behavior as monolithic closure
in both full-copy and shared-graph-pages branches?

## Design

Six cases cover a retained predecessor interface, wrong speaker, a
topic-bearing intervening event, an eligible topicless chain, a missing
predecessor edge, and an omitted target interface. Five execution arms are
compared for each case in three fresh workers: monolithic closure on the
primary; monolithic closure in a full-copy branch; monolithic closure in a
shared-graph-pages branch; scoped closure in a full-copy branch; and scoped
closure in a shared-graph-pages branch. The prior instruction and its
action-target interface are settled before the current correction is added.
Each scoped branch owns the current event and its correction interpretation;
the predecessor remains globally readable.

Branch arms capture a source revision, fork an immutable snapshot, start a
delta journal, checkpoint the materialized input as the derivation baseline,
close rules, extract the derived-only residual, verify the
primary graph/rules/revision remain unchanged, and apply the residual against
the captured revision. The final primary graph must match the entire branch
graph and the monolithic primary graph canonically. The source lock includes
the runner, independent analyzer, seed, discourse-state materializer,
snapshot/delta APIs, graph storage, and rule matcher; a post-run hash equality
gate rejects source drift.

## Pass criteria

- All five arms agree on complete canonical graph state and exact correction
  status/evidence for every case.
- Retained-interface and topicless-chain cases ground; each negative control
  remains unresolved.
- Every branch leaves its primary graph, rule store, and revision unchanged
  until residual application.
- Revision-checked residual application succeeds and reproduces branch graph
  state exactly, for both backends and both closure modes.
- All source-lock, workload-matrix, and independent-analysis checks pass.

Timing is exploratory and reported by phase; this protocol has no speedup
threshold. It measures one authored communication family and does not test
learned boundaries, natural-task prevalence, or capability acquisition.

## Artifacts

- Runner: [thoughtexperiment_predecessor_cow_residual_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_cow_residual_v1.py)
- Analyzer: [analyze_thoughtexperiment_predecessor_cow_residual_v1.py](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_cow_residual_v1.py)
- Source lock and capture are produced by `--lock` and the runner; analysis is
  produced by the independent analyzer.
