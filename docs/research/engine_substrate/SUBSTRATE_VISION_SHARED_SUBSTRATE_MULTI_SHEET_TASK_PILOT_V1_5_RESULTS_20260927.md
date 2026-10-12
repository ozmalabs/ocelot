# Shared-substrate multi-sheet fixed-frame diagnostic v1.5 results

## Outcome

The source-locked root-scoped diagnostic passes all nine independent analysis checks. From the same prepared graph snapshot, the exact B phase-zero, orientation-zero grating evokes positive endpoint `act` in all 16 B SUnits: total activation is 295.1451 (19.1194 maximum per unit). With A blank, B receives all 128 retinal bursts. With the registered A grating active at the same time, B's per-unit `act` vector is exactly identical. B has zero `rate` in both grating conditions. Both blank sheets have zero B activation; A-only stimulation leaves B inactive.

This rejects measurable A-to-B suppression in this single fixed-frame, root-scoped endpoint comparison. V1.4's “joint B activity” check inspected positive `rate` during a full K=16 A readout; that metric remained zero and did not establish that B's `act` was zero under the exact paired frame. The apparent contradiction is therefore a difference in endpoint protocol and field, not evidence of a scope-dependent effect. V1.6 subsequently showed that each exact-frame activation is below its learned `theta`; therefore zero `rate` is exactly what the threshold rule predicts in this endpoint.

| Condition | A retinal bursts | B retinal bursts | B rate sum / active units | B act sum / active units | Closure |
|---|---:|---:|---:|---:|---|
| Both blank | 0 | 0 | 0 / 0 | 0 / 0 | fixed point |
| B exact grating only | 0 | 128 | 0 / 0 | 295.1451 / 16 | repeated graph state |
| A exact grating only | 128 | 0 | 0 / 0 | 0 / 0 | repeated graph state |
| Both exact gratings | 128 | 128 | 0 / 0 | 295.1451 / 16 | repeated graph state |

A `repeated_graph_state` is a terminal rule-report status under the captured engine API, not a budget exhaustion. All conditions restored the same prepared-state digest. Retinal ON/OFF channels remained active after adaptation, source fingerprints matched, and every condition's closure stayed within the registered cumulative progress limit.

## Interpretation and next gate

The fixed-frame evidence supports stimulus propagation through B's retinal and SUnit stack and shows no detectable change in B endpoint activation from adding A's grating. It does not demonstrate general frame-locality or safe partitioning: one paired stimulus, one seed, one small anatomy, one settling mode, and endpoint values only. Nor does it show that inference/readout `rate` is functioning as expected when `act` is positive.

V1.6 has completed the threshold audit for the root-scoped exact-frame endpoint. Next replicate the four-condition control under global settling and broaden the orientation/phase response panel with explicit `act` and `rate` equations before any scale or prevalence claim.

## Evidence

- [Raw capture](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_5.py)
- [Preregistration](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_5_PREREG_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_5_lock_20260927.json)

This result is a diagnostic on a single synthetic fixture, not an estimate of natural-task prevalence, general tractability, or scale behavior.
