# Vision default-tick latency-filter probe preregistration

Date: 2026-09-25. Read-only source audit plus one native runtime probe; no seed or engine changes.

## Question
Does the zero-progress response to a grating written into a built vision graph result from missing attr notification, or from default cycle-plan latency filtering?

## Method
Build one 3×3 lateral `settle_lib.build_sheet` with seed 20260925. Read enabled `DualProcessPolicy` state and `export_rules()` latency metadata for `st_settle`, `st_commit`, `oo_sunit_activate`, `oo_sunit_rate`, `lat_pool`, `lat_residual`, and `lat_bipolar`. Confirm source routing in `cognitive_cycle.rs`: default selects DualProcess when a policy is enabled; DualProcess runs the `hard_realtime` class. Write one 0-degree grating exactly as the established presenter does, call `tick(200000, false)`, then call unfiltered `run_rules_report(200000, true)` on the same graph. Record progress, status, act/rate maxima, and hashes.

## Prediction
If vision rules are untagged while dual-process policy is enabled, default tick can skip them; full rescan should then progress and produce responses. This identifies a default-plan routing/classification mismatch for this workload, not an attr invalidation defect. Runtime findings may falsify this prediction. This probe does not change policy or assign latency classes.
