# Thoughtexperiment predecessor fanout current-source replay v1 — results

Date: 2026-10-04

## Result

The six-worker source-locked replay passes all ten independent analysis gates.
It uses four independent-state frames, four supplied candidate branches,
100,000 unrelated noise nodes, three fresh workers per backend, and the current
native extension hash recorded in the lock (`1d00db8812fb…`). All six workers
select only the correct candidate. Branch and returned-primary graphs match an
independent direct monolithic oracle; primary state remains isolated before
return; active rules are preserved; stale residual retries are rejected without
mutation; and all candidate scoped closures reach quiescence.

The graph has a median of 100,511 nodes and 467 edges. Median candidate-fork
time is 75.0 ms for full-copy and 0.574 ms for shared graph pages, about a 131×
difference in this specific measured phase. Median full lifecycle is 3.13 s and
3.21 s respectively. Thus this run confirms the large fork-cost difference but
does not show an end-to-end lifecycle advantage for shared pages. There are
three replicates per backend, so the small lifecycle difference is descriptive.

The existing named timers account for 97.6 ms (3.0%) of full-copy lifecycle and
5.17 ms (0.16%) of shared-page lifecycle at the median. The remaining 3.03 s and
3.20 s are outside those timers. The capture does not instrument graph export,
canonical digesting, or every validation step individually; the remainder must
not be attributed to any one of these operations. A follow-up needs direct
timers for export, digest, oracle checks, and memory sampling before diagnosing
the dominant cost.

## Claim boundary

This is a current-source confirmation of one authored 100k-node workload on
one host. It does not measure natural task prevalence, open candidate
generation, concurrent experiments, or a scaling law. Candidate construction
and the task oracle are supplied by the harness. The prior 100k capture was
exploratory and did not retain its runner/source lock; this replay is the
reproducible evidence for this configuration.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_CURRENT_SOURCE_REPLAY_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_current_source_replay_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_current_source_replay_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_20261004.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_current_source_replay_v1_analysis_20261004.json)
