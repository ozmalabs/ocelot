# Shared-substrate matched-scope endpoint comparison v1.7 results

## Capture validity

The matched-scope capture passes all eight independent integrity checks. Both rule variants restore the same prepared graph digest, Retina/SUnit identities match, all four conditions deliver the declared retinal burst counts, source fingerprints remain stable, update stamps match the scheduled endpoint, and closures finish within the 1.6M progress bound. One root-scoped-adapted graph is used for both endpoint arms, so the result isolates the endpoint rule variant conditional on that state. It does not compare global versus root-scoped learning histories.

## Measured endpoints

B's `act` differs sharply across rule variants:

| Condition | Root-scoped B `act` sum | Global-rule B `act` sum | Root status | Global status |
|---|---:|---:|---|---|
| Both blank | 0 | 0 | fixed point | fixed point |
| B grating only | 295.1451 | 590.2902 | repeated state | repeated state |
| A grating only | 0 | 0 | repeated state | fixed point |
| Both gratings | 295.1451 | 0 | repeated state | fixed point |

The B grating produces 128 retinal bursts in both B-stimulated conditions. With root-scoped settling, B's per-unit `act` vector is identical when A is blank or stimulated. Under the global rule, B's endpoint activation changes when A is added: the B-only case has all 16 units active, while the both-gratings case ends at a fixed point with zero B `act`. The global B-only sum is exactly twice the root-scoped sum in this captured state.

This is evidence of cross-sheet coupling in the global-rule dynamics on this one graph. It is **not** a settled-response equivalence result: three root-scoped conditions and global B-only terminate by repeated-state detection rather than a fixed point. Those endpoints are captured points on deterministic cycles. In particular, the comparison between global B-only's cycle and global both-gratings' fixed point says that the added A stimulus changes the dynamical regime; it does not establish what a converged B response would be if those cycles were resolved differently.

## `act` and `rate` are different time-slice measurements

Across the 256 per-unit observations (both sheets, four conditions, two scopes), 76 final `rate` values differ from `max(final act - theta, 0)`. Blank conditions and B's positive root-scoped B-only/both endpoints match, but mismatches occur in stimulated A and global conditions. This fails the preregistered semantic consistency gate; it is distinct from the passing capture-integrity checks. The update stamps are current, yet the fields can still refer to different moments in the closure: the `oo_sunit_rate` rule writes `rate=max(act-theta,0)` once when `rate_step < Retina.step` and `act_step == Retina.step`, then stamps `rate_step` to that step. `st_settle` can subsequently rewrite `act` without incrementing the Retina step or reopening the rate guard. Thus equal stamps do not prove `rate` was computed from the final settled `act`.

V1.6 established the threshold equation only for B units in its two exact-frame root-scoped conditions; it did not justify treating final `act` and `rate` as a general equation across the settled graph. The matched comparison has surfaced a field-timing issue that must be resolved before using `rate` as a task endpoint.

## Next gate

V1.8 has completed passwise traces and exact cycle enumeration for all eight scope/condition cells. It finds a field timing distinction and scope-dependent fixed-point/cycle outcomes. Next specify the response phase contract, then repeat across seeds and a broader, independently authored stimulus panel; preserve fixed points and cycles as separate outcomes.

## Evidence

- [Raw capture](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_20260927.json)
- [Prepared graph checkpoint](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_prepared_graph_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_7.py)
- [Preregistration](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_7_PREREG_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_7_lock_20260927.json)

One learned state, one seed, 16 SUnits per Retina, four endpoint conditions, and one-sided root-scoped adaptation do not establish general scope safety, natural-task locality, or scaling.
