# Response-priority residual-continuation v1.2.1: counterbalanced cost result

Date: 2026-10-06  
Status: eight-worker same-family replication passed; timing direction repeated in all four pairs.

## Result

Four fresh worker pairs used the preregistered alternating order (global/priority, priority/global, global/priority, priority/global). The capture passed worker/source-lock integrity and all semantic parity, cardinality, and convergence checks. Every pair retained reply and graph parity across all seven turns; all continuations reached zero residual without the round cap.

| Measure | Global median | Priority median |
|---|---:|---:|
| Response path, 28 turns | 135.157 ms | 123.812 ms |
| Continuation, 28 turns | 7.041 ms | 7.009 ms |
| Paired response + continuation, 28 turns | 143.585 ms | 130.973 ms |

Within each paired replicate, the median total response-plus-continuation time was lower for priority by 6.44–10.29% (four of four pairs), regardless of which arm ran first. This reduces the concern that the previous six-worker result came from arm order alone. It remains one authored held-topic family on one machine. The timing describes the adapter response path, not an isolated native-kernel benchmark.

The evidence supports a repeatable cost signal on this partition and task family, with finite semantic parity. It does not establish natural-task prevalence, performance on other task families, an asymptotic advantage, or low cost for learning new structure. The next gate is to replay the same partition over independently authored live-conversation routes and retain each route's utility check.

## Artifacts

- [Preregistration](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_1_COUNTERBALANCED_PREREG_20261006.md)
- [Runner](../../../scripts/substrate_response_priority_residual_continuation_v1_2_1_counterbalanced_20261006.py)
- [Analyzer](../../../scripts/analyze_response_priority_residual_continuation_v1_2_1_counterbalanced_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_residual_continuation_v1_2_1_counterbalanced_20261006_lock.json)
- [Compact capture](../../../evaluation/reports/response_priority_residual_continuation_v1_2_1_counterbalanced_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/response_priority_residual_continuation_v1_2_1_counterbalanced_analysis_20261006.json)
