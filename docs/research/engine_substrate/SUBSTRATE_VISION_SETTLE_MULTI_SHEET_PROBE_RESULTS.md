# Vision settling multi-sheet coupling probe

**Run:** 2026-09-25. **Evidence type:** native runtime semantic probe on two minimal world-rooted SUnit pairs. **Runner:** [`substrate_vision_settle_multi_sheet_probe_v1_2.py`](../../../scripts/substrate_vision_settle_multi_sheet_probe_v1_2.py). **Independent analyzer:** [`analyze_substrate_vision_settle_multi_sheet_probe_v1_2.py`](../../../scripts/analyze_substrate_vision_settle_multi_sheet_probe_v1_2.py).

## Preserved setup history

V1 loaded the seed's existing `SettleParams` and accidentally added a second, correctly triggering `PickUnique`'s ambiguity panic before raw output. V1.1 reused the singleton and showed the predicted A outputs, but one arm made no progress because its scratch `act_next` already equalled the expected output. These attempts and locks are retained: [v1 runner](../../../scripts/substrate_vision_settle_multi_sheet_probe.py), [v1 lock](../../../evaluation/substrate_capability/vision_settle_multi_sheet_probe_lock_20260925.json), [v1.1 raw](../../../evaluation/reports/substrate_vision_settle_multi_sheet_probe_v1_1_20260925.json), [v1.1 analysis](../../../evaluation/reports/substrate_vision_settle_multi_sheet_probe_v1_1_analysis_20260925.json), and [v1.1 lock](../../../evaluation/substrate_capability/vision_settle_multi_sheet_probe_v1_1_lock_20260925.json).

The v1.2 amendment initializes the scratch output buffer to -1.0, forcing a native write in both arms while leaving inputs and predicted outputs unchanged. Protocol and lock: [v1.2 amendment](SUBSTRATE_VISION_SETTLE_MULTI_SHEET_PROBE_V1_2_AMENDMENT_20260925.md), [lock](../../../evaluation/substrate_capability/vision_settle_multi_sheet_probe_v1_2_lock_20260925.json).

## Result

The sole loaded rule was the authored batched `st_settle`. Two separate `World` roots each owned a pair of SUnits. Sheet A had `act=[1,1]` in both arms; sheet B was `[0,0]` or `[1,1]`; all `aff` values were zero. Both arms made one progress application and reached the registered outputs:

| Sheet B input | Sheet A `act_next` | Sheet B `act_next` |
|---|---|---|
| `[0,0]` | `[0.5,0.5]` | `[0,0]` |
| `[1,1]` | `[0,0]` | `[0,0]` |

The independent analyzer recomputed the global means and verified both outputs, lock provenance, current-source engine provenance, and cross-arm change. This confirms the seed's global `NodesOfType(SUnit)` fold couples separate `World` roots that share one substrate: B's state changes A's computed response. The seed's source-level read does not restrict the global fold to the matched root `r`.

## Limits and next gate

This is a minimal semantic probe, not two full cortical sheets. It establishes cross-world coupling for the exact two-pair fixture; no run-time cost or full-sheet behavior was measured. The static census separately shows complete dependency width within one sheet because the same fold reads all SUnits.

The seed comments describe mean competition over one sheet, while the implementation folds all graph SUnits. Test the proposed root-scoped interpretation on full `settle_lib.build_sheet` constructions before changing the seed. If per-sheet competition is intended, compare current global-fold and root-scoped arms on identical full graphs for terminal states, residual, orientation/task outcomes, and cost. This requires a frame-aware aggregate or a term that folds `r`'s `has_sunit` members; it does not make spatial partitions independent within a sheet.
