# Thoughtexperiment predecessor fanout cost breakdown v1 — results

Date: 2026-10-04

## Result

All six source-locked workers pass the ten independent gates. The measurement
repeats the current-source four-frame/four-candidate/100,000-noise-node
workload, with three fresh processes per snapshot backend. Candidate outcomes,
oracle graph parity, primary isolation, active-rule preservation,
stale-revision rejection, and scoped closure quiescence remain intact under the
instrumentation.

The new timers observe five `Substrate.graph_to_dict` exports and five
`canonical_graph_digest` calls inside each lifecycle interval. Median graph
export time is 2.43 s (full-copy) and 2.45 s (shared pages); median canonical
digest time is 737 ms for both. Median named phases account for 103.6 ms and
5.45 ms respectively, and the residual unattributed time is about 137 ms and
135 ms. Across the three workers, graph export accounts for a median 71.8% and
73.5% of lifecycle time, while canonical digest accounts for 20.8% and 22.1%.
These costs explain most of the multi-second lifecycle in this fixture and
show why fast branch creation did not produce an end-to-end advantage.

The timers wrap the Python graph-export and digest functions while the base
worker's lifecycle timer is active. Clock interception adds measurement
overhead; there is no matched instrumentation-off arm in this six-worker run.
The result attributes cost to these functions, not their internal native
sub-operations, and does not establish how much of the time is reducible.

## Claim boundary

One authored graph shape and one host, with four frames and four supplied
candidates. No natural workload prevalence, candidate-generation ability,
concurrent experiment throughput, or general scaling law is established.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_COST_BREAKDOWN_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_20261004.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_analysis_20261004.json)
