# Response-priority residual-continuation v1.2: operational-cost result

Date: 2026-10-06  
Status: six-worker diagnostic completed; parity gates passed; cost result is workload-specific.

## Measurement

The source-locked panel ran 21 turns in each arm (three fresh workers per arm, seven turns each). Per-rule mutation-attribution journaling was disabled. The source lock and worker inputs matched; all 71 reply, outcome, graph-parity, cardinality, and convergence checks passed. Full seed boot was measured separately at medians of 12.128 seconds global and 12.056 seconds priority and is excluded from turn costs.

| Measure, median across 21 worker-turns | Global | Priority |
|---|---:|---:|
| Adapter response path | 136.054 ms | 125.099 ms |
| Continuation | 7.366 ms | 7.522 ms |
| Response + continuation, paired per turn | 143.562 ms | 133.201 ms |
| Normalized graph parity and zero residual | Pass | Pass |

On this capture, the paired total median is about 7.2% lower for priority. The arm order was fixed (global workers first, priority workers second), and only one held-topic task family and one machine were measured. Treat the difference as a signal for replication, not a general speed result. The response timing includes the normal adapter path and is not a pure native-kernel timer.

## Work distribution

The priority response report recorded a median of six selected-settlement calls, 20,408 rule attempts, and 29 progressing steps per turn. Its final selected residual had a median of four dirty ambient rules; continuation cleared them with a median of zero progressing steps. The `RuleFiringHistory` gate remained equal after continuation.

The separate scale-audit counters show fewer term evaluations (median 207,065 versus 605,548) and fewer where evaluations (21,429 versus 56,209) for priority, but more rule enumerations (20,444 versus 17,010). Graph writes had a median of 241 in both arms. This mixed profile fits the observed phase shift: the priority schedule avoids some evaluation work during response and pays a small later continuation, while still enumerating more candidates overall. It does not establish improved asymptotic complexity or CPU efficiency on other tasks.

## Next gate

Replicate the timing signal with counterbalanced arm order and additional independently sampled task families. Measure frame aperture and actual cross-frame reads alongside response/continuation cost. Keep held-structure application separate from rung 3/4 acquisition; this result says nothing about the cost of learning new structure.

## Artifacts

- [Preregistration](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_COST_PREREG_20261006.md)
- [Runner](../../../scripts/substrate_response_priority_residual_continuation_v1_2_cost_20261006.py)
- [Analyzer](../../../scripts/analyze_response_priority_residual_continuation_v1_2_cost_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_residual_continuation_v1_2_cost_20261006_lock.json)
- [Capture](../../../evaluation/reports/response_priority_residual_continuation_v1_2_cost_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/response_priority_residual_continuation_v1_2_cost_analysis_20261006.json)
