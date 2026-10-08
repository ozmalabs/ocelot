# Access-trace overhead replay v1 results

Date: 2026-10-03

## Outcome

The randomized matched replay completed three replicate pairs across six fresh processes. All ten capture gates pass: source locks remained stable; each pair reproduced the same semantic graph digest and task outcomes; scheduler/work trace rows matched exactly within each pair; the on arm recorded concrete events while the off arm recorded none; all work/access drop counters were zero; and existing semantic controls passed.

The request-time paired ratios are descriptive:

| Prompt | Median on/off ratio | Paired range | Median on time | Median off time |
|---|---:|---:|---:|---:|
| `report your organisation` | 1.019 | 0.986–1.029 | 8.43 s | 8.28 s |
| `describe who you are` | 1.109 | 1.010–1.145 | 8.48 s | 7.64 s |

Across six requests per arm, the on arm recorded 279,024 aggregated access-event rows, including 4,137 direct `NodesOfType` rows; the off arm recorded zero concrete access rows. Scheduler/work tracing remained enabled in both arms. The timer covers `WorldAdapter.converse` execution, including concrete event recording, but stops before access-trace snapshot extraction, serialization, or archiving.

At n=3 pairs per prompt, the results indicate a small overhead on one prompt and a larger, variable overhead on the other. One pair for the first prompt is slightly below 1.0, so the data do not support a universal percentage or a statistically strong estimate. This is one authored fixture, and the 7.6–8.8 second request latency includes the entire adapter task path; it is not a clean isolated engine microbenchmark.

## Reproduction artifacts

- Protocol: [overhead preregistration](SUBSTRATE_ACCESS_TRACE_OVERHEAD_V1_PREREG_20261003.md)
- Runner: [paired capture runner](../../../scripts/substrate_access_trace_overhead_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/access_trace_overhead_v1_lock_20261003.json)
- Raw paired workers: [compressed archive](../../../evaluation/reports/access_trace_overhead_v1_workers_raw_20261003.json.gz)
- Capture summary: [machine-readable summary](../../../evaluation/reports/access_trace_overhead_v1_20261003.json)
- Independent hash/timing recomputation: [analysis](../../../evaluation/reports/access_trace_overhead_v1_analysis_20261003.json), [analyzer](../../../scripts/analyze_access_trace_overhead_v1.py)

## Next gate

Increase matched repetitions and add a lightweight-trace arm that records query/candidate cardinalities without full concrete-row aggregation. Retain graph, scheduler, and lifecycle parity gates. Then cover rejected matcher candidates and evaluate candidate frame partitions against monolithic closure with complete discovery and execution costs.
