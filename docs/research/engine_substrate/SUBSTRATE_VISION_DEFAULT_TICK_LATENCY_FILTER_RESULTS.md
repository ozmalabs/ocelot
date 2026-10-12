# Default tick filtering of vision rules

**Run:** 2026-09-25. **Evidence:** source-linked native runtime probe and independent audit. No seed or engine changes.

## Finding
The built substrate contains an enabled `DualProcessPolicy`. The default cycle dispatcher selects `CyclePlan::DualProcess` when that policy is enabled; that plan runs the `hard_realtime` latency class. The loaded `st_settle`, `st_commit`, `oo_sunit_activate`, `oo_sunit_rate`, `lat_pool`, `lat_residual`, and `lat_bipolar` rules have empty latency classes.

On one written grating frame, default `tick(200000, false)` made zero progress. Running unfiltered `run_rules_report(200000, true)` on the same graph made 111 progress applications, ended with `repeated_graph_state`, and produced max SUnit act 28.458 and rate 28.443. This supports a default plan/rule-class mismatch for this workload. It does not support the earlier hypothesis that host writes failed to notify rules: default-plan filtering explains the observation, and no notification defect was isolated.

## Evidence
- Source path: [`cognitive_cycle.rs`](../../../runners/dsl/src/cognitive_cycle.rs) selects DualProcess under an enabled policy; DualProcess invokes `run_rules_latency_opts` for `hard_realtime`. [`substrate.rs`](../../../runners/dsl/src/substrate.rs) filters active rules by exact latency class.
- [`preregistration`](SUBSTRATE_VISION_DEFAULT_TICK_LATENCY_FILTER_PREREG_20260925.md), [`runner`](../../../scripts/substrate_vision_default_tick_latency_filter_probe.py), [`analyzer`](../../../scripts/analyze_substrate_vision_default_tick_latency_filter_probe.py)
- [`raw report`](../../../evaluation/reports/substrate_vision_default_tick_latency_filter_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_default_tick_latency_filter_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_default_tick_latency_filter_lock_20260925.json)

## Next gate
Measure a benchmark-only rule-metadata variant that tags the required vision pipeline as `hard_realtime` and compare default `tick` against full-rescan closure on the same frame sequence, with state, response and cycle-status parity. Do not alter production latency metadata until that end-to-end gate passes.
