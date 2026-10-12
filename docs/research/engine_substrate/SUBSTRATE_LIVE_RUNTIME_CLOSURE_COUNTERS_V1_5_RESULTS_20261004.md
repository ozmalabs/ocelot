# Live runtime closure counters v1.5 — results and limits (2026-10-04)

## Outcome

The source-locked 3-replicate × 2-mode capture completed all six workers successfully. The corrected audit-off isolation gate passes for all six requests: global counters and every attribution table are empty. The paired requests retain task and reply parity, one semantic graph digest, zero dropped access/work events, and complete runtime rule resolution (4,788 of 4,788 RuleUID observations). Delegated producer-event rows remain present in the task capture, and the per-request setter trace finds no nested mode changes.

The independent analyzer fails six gates, all from unattributed Term work in the audit-on arm: each replicate has 145 evaluations on `report your organisation` and 134 on `describe who you are`. Unattributed candidate tests are zero; candidate, clause, semantic-edge, and first/repeat conservation pass. This isolates the remaining issue to Term attribution rather than audit-off leakage or matcher attribution. Variant totals show the missing Term evaluations span `And`, `Argmax`, `Attr`, `Eq`, `Exists`, `In`, `Lit`, `Neighbours`, `NodesWhere`, `Plus`, `ReachableFrom`, `TextShape`, `Times`, and `Var`; these counts describe missing rule ownership, not a causal source diagnosis.

## Interpretation

The v1.4 audit-off anomaly is resolved as harness overlap: its base task worker enabled/reset the same process-global counters for producer-event submeasurements. V1.5 delegates those nested audit operations to the outer request scope while preserving event creation and task semantics. Audit-off zero-count behavior now holds on the actual live route.

V1.5 is still not a complete per-rule Term-cost result. The selected route has 279 unattributed Term evaluations across its two prompts in every audit-on replicate (145 + 134); no per-rule workload cost claim should absorb them into a named rule. The next step is to distinguish direct host-requested evaluation from matcher-context loss and attribute/classify each source, then repeat the locked panel. The capture does not estimate natural task prevalence, total CPU cost without instrumentation, or asymptotic scaling.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_5_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_5.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_5.py)
- [Source lock](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_5_lock_20261004.json)
- [Six-worker capture](../../../evaluation/reports/live_runtime_closure_counters_v1_5_20261004.json.gz)
- [Independent analysis](../../../evaluation/reports/live_runtime_closure_counters_v1_5_analysis_20261004.json)
