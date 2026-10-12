# Response-priority residual-continuation v1.2: confirmatory result

Date: 2026-10-06  
Status: confirmatory finite semantic-parity gate passed for the preregistered held-topic workload.

## Result

Six fresh workers completed the seven-turn workload: three global and three priority. The source lock matched the capture, inputs remained stable, and all workers used `PYTHONHASHSEED=0`. All 71 analyzer checks passed.

At every turn, replies and held-topic outcome projections matched between arms and repeated within each arm. Normalized graph fingerprints and node/edge cardinalities matched both between arms and across workers. The counts grew from 25,068 nodes / 11,507 edges after turn zero to 25,390 nodes / 12,265 edges after turn six, identically across arms. All continuations reached zero residual without a round-cap hit. Each worker's first-turn conceptualizer produced a committed intent, and selected reports included canonical `global`.

The graph parity gate covers the firing-history ledger's non-ID fields as well: the semantic fingerprint retains ordinary attributes such as the last rule and settlement sequence, while normalizing NodeID references. The source fix records the last progressing selected rule before the host commits the turn ledger.

This supports finite semantic parity for this one held-topic family, this rule partition, and the measured seven-turn horizon. It does not demonstrate natural-task prevalence, general tractability, or a latency advantage. The timing instrumentation was enabled: median response elapsed time was 127.5 ms for global and 133.8 ms for priority, with a 7.2 ms median priority continuation. These instrumented figures are descriptive and not a performance result.

## Next measurement

The separate mutation-journaling-off cost comparison has now completed and is reported in [cost results](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_COST_RESULTS_20261006.md). Next replicate the timing signal with counterbalanced arm order and additional independently sampled task families; record frame aperture and cross-frame reads. This confirmation alone cannot support an architecture-wide scheduling claim.

## Artifacts

- [Preregistration](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_CONFIRMATORY_PREREG_20261006.md)
- [Runner](../../../scripts/substrate_response_priority_residual_continuation_v1_2_confirmatory_20261006.py)
- [Analyzer](../../../scripts/analyze_response_priority_residual_continuation_v1_2_confirmatory_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_residual_continuation_v1_2_confirmatory_20261006_lock.json)
- [Capture](../../../evaluation/reports/response_priority_residual_continuation_v1_2_confirmatory_20261006/capture.json.gz)
- [Analysis](../../../evaluation/reports/response_priority_residual_continuation_v1_2_confirmatory_analysis_20261006.json)
