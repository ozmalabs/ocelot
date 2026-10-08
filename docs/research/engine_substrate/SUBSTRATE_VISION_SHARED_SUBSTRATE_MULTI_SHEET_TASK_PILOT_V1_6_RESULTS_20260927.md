# Shared-substrate SUnit rate-threshold audit v1.6 results

## Outcome

The source-stable root-scoped rerun passes all nine independent checks. On the exact B grating, all 16 B SUnits have positive `act` (17.688–19.119), but their learned thresholds are higher (20.282–20.739), so the registered rate rule predicts zero for every unit. The observed `rate` vector exactly matches `max(act - theta, 0)` with zero mismatches in both B-only and simultaneous A/B grating conditions. Every unit's `act_step` and `rate_step` equals the schedule-implied endpoint step 23,010.

This resolves the v1.4/v1.5 field discrepancy for the root-scoped exact-frame endpoint: positive activation with zero firing rate is the expected consequence of threshold rectification, not evidence of missing B input or B-stack silence. Adding A's stimulus leaves B's per-unit activation exactly unchanged. The result remains fixture-specific and does not establish global-scope equivalence or a general visual capability claim.

| Measure, B SUnits | Exact-frame range or value |
|---|---:|
| `act` | 17.688–19.119 |
| `theta` | 20.282–20.739 |
| `max(act − theta, 0)` | 0 for all 16 |
| Observed `rate` | 0 for all 16 |
| `act_step`, `rate_step` | 23,010 for all 16 |
| Threshold-equation mismatches | 0 / 32 observations |
| Stale update stamps | 0 / 32 observations |

The endpoint step is derived from 3,000 development steps, 2,000 paired presentations advancing each Retina by 10, then one 10-step probe increment. Each condition restores the same adapted graph before applying its probe.

## Capability interpretation and next work

The measurement pipeline now distinguishes stimulus arrival (`retinal bursting`), simple-unit drive (`act`), thresholded response (`rate`), and their update-step stamps. That is a useful instrumentation correction for capability benchmarking: a zero in one field cannot stand in for absence of processing without following its writer and threshold semantics.

Next replicate the exact four conditions under global settling from a separately prepared, identical seed state, then test a small preregistered orientation/phase set and compare both `act` and `rate` against the independent equations. Only after scope parity and stimulus-response validity are established should the task family be widened or scaling be claimed.

## Evidence

- [Raw capture](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_6_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_6_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_6.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_6.py)
- [Preregistration](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_6_PREREG_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_6_lock_20260927.json)

This result is one synthetic seed, 4×4 units per Retina, root-scoped settling, and four controlled presentations. It does not estimate natural-task prevalence, general tractability, or scale performance.
