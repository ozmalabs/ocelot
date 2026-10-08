# Native visual rule-phase trace v1 results (2026-09-29)

## Result

The opt-in native observer passes its default-tick parity gate on all six seed/scope pairs. Each pair runs the default and traced `WaveWorld.step(frame=...)` path with a 0° phase-0 grating on sheet A and a blank on sheet B. Final graph SHA-256 digests match exactly after both adapter calls in every pair. The capture contains 1,001 rule events, including one `oo_sunit_rate` event per adapter call, with no truncation. All 10 independent integrity and measurement checks pass.

For 384 sampled SUnits whose activation and rate update stamps match, the post-rule `rate` differs from `max(act-theta, 0)` in 88 samples at tolerance 1e-9; the median absolute residual is 0 and the maximum is 1.47329. The trace is taken after a complete rule invocation over its bindings, so this is not evidence that the rule equation is wrong: other bindings can update state during the invocation. It shows that matching update stamps do not identify a unique per-binding write phase. The observer establishes phase-local access at whole-rule granularity only.

Median worker wall time is 0.299 s default and 0.305 s traced; median process CPU is 0.298 s and 0.305 s. Peak RSS is 141.7 MB and 145.4 MB respectively. This is a small diagnostic panel, not a calibrated service-cost estimate. The trace API's observer cost is modest in these fixtures, but no general overhead bound follows.

## Scope and limits

The result demonstrates that the native observer can run within the same default cognitive-cycle plan as `WaveWorld.step` while preserving exact final graph state for three adapted checkpoints, two settlement scopes, and one synthetic grating/blank sequence. It resolves the prior inability to observe the `oo_sunit_rate` phase through the adapter's final state alone, subject to whole-rule granularity. It does not establish natural-image recognition, an equation-level correctness result, frame discovery, task prevalence, or scaling to larger graphs. The broader cheap-cut hypothesis remains untested as a natural-task distribution claim.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_VISION_NATIVE_RULE_PHASE_TRACE_V1_PREREG_20260929.md)
- Runner: [capture script](../../../scripts/substrate_vision_native_rule_phase_trace_v1.py)
- Analyzer: [independent analyzer](../../../scripts/analyze_substrate_vision_native_rule_phase_trace_v1.py)
- Raw capture: [worker data](../../../evaluation/reports/vision_native_rule_phase_trace_v1_20260929_raw.json)
- Analysis: [machine-readable results](../../../evaluation/reports/vision_native_rule_phase_trace_v1_20260929_analysis.json)
- Input lock: [source and checkpoint lock](../../../evaluation/substrate_capability/vision_native_rule_phase_trace_v1_20260929_lock.json)

