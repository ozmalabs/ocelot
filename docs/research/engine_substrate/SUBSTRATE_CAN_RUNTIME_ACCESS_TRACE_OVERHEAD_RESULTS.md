# CAN runtime access-trace overhead

**Run date:** 2026-09-25  
**Evidence grade:** paired instrumentation-cost envelope on one authored workload  
**Status:** all 192 runs pass state/progress parity and independent fixed-point gates; paired timing arithmetic independently rechecked.

## Protocol

The preregistered [four-arm protocol](SUBSTRATE_CAN_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md) compares `plain`, `scale_only`, `trace_only`, and `both` on 48 deterministic CAN instances: N=8/16 × path/complete × two-/three-state × six seeds. Arm order rotates by replicate. Timing covers only native `run_rules(100_000)`; fixture construction and readback are outside the interval. The trace is disabled and reset between arms. The 192 arm runs use the same generated graph for each four-way comparison.

## Results

All six registered checks pass: all four arms match exact final state and progress per instance; every arm reaches zero terminal progress and passes the independent local fixed-point oracle; trace arms have no dropped or statically unexplained events; disabled trace arms emit none; trace-only arms have no scale-audit counters; and scale-only arms have counters but no trace events. The separate v1 CAN capture established per-rule counter conservation at every traced site. The independent analyzer recomputes all eight cell summaries from raw paired timings and verifies the runner’s arithmetic.

Across the eight workload cells, the median of cell-level paired `trace_only/plain` wall-time ratios is **1.15×**, with cell medians from **1.09× to 1.27×**. Median plain closure times range from roughly **0.30 ms to 2.32 ms**; trace-only medians range from **0.32 ms to 3.27 ms**. The path N=16 two-state cell contains one paired ratio of 4.47×, visible in the raw replicates; this and the very short baseline durations make the small-run spread material.

For context, per-rule scale audit alone has a median of cell-level paired wall ratio **2.80×** (2.38×–3.01×). With scale audit already enabled, adding the trace (`both/scale_only`) has median ratio **1.05×** across cell medians (1.04×–1.12×). Do not use the latter as the standalone trace overhead; `trace_only/plain` is the isolated comparison. CPU ratios closely track wall ratios in this single-process workload.

Raw 48-cell/192-arm capture and provenance: [`substrate_can_runtime_access_trace_overhead_v1_1_20260925.json`](../../../evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_1_20260925.json). Independent arithmetic audit: [`analysis JSON`](../../../evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_1_analysis_20260925.json), [`analyzer`](../../../scripts/analyze_substrate_can_runtime_access_trace_overhead_v1.py), and [`runner`](../../../scripts/substrate_can_runtime_access_trace_overhead_v1.py). The first v1 output used ratio-of-arm-medians aggregation and is retained at [`v1 diagnostic`](../../../evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_20260925.json); v1.1 uses medians of within-instance paired ratios as preregistered and supersedes that summary.

## Interpretation and limits

The trace adds measurable cost on this small CAN envelope, with a median around 15% relative to uninstrumented closure. This is not a general overhead guarantee: only one host and one workload family are covered, the absolute operations are small, and the event stream is partial. Larger graphs may change the ratio because tracing costs scale with emitted reads/writes and currently use a mutex-backed bounded map. The scale-audit comparison confirms that the trace can be evaluated separately from the substantially heavier per-rule counter path.

This experiment does not establish frame locality, trace completeness, decomposition quality, partition preservation, or useful-scale CPU feasibility. Next apply the same event coverage and paired overhead protocol to a preregistered conversation workload, then test candidate cuts against monolithic closure and omitted-boundary controls.
