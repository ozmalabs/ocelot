# Conversation runtime access-trace overhead

**Run date:** 2026-09-26 (refresh)  
**Evidence grade:** paired instrumentation-cost diagnostic on one authored workload  
**Status:** 48 closure runs across 12 fixtures pass outcome/fixed-point and instrumentation-isolation gates; paired timing summary independently recomputed.

## Protocol and results

The fixed [protocol](SUBSTRATE_CONVERSATION_RUNTIME_ACCESS_TRACE_OVERHEAD_PREREG_20260925.md) compares `plain`, `scale_only`, `trace_only`, and `both` on one- and two-deliberation inputs, six replicates per size. Timing covers only `run_rules_report(100_000)`. Arm order rotates by replicate. All paired projections, progress, and fixed-point results match. Trace arms have no overflow or static access mismatch; all measured event sites in the combined arm reconcile with per-rule audit counts. An independent analyzer recalculates medians, ranges, and paired ratios from the raw arm timings.

The latest capture against native build `a6aac84f41ed` gives a median trace-only/plain paired wall ratio of **1.15×** (range **0.69×–1.17×**) for one deliberation; median plain wall time is about **0.059 ms**. For two deliberations, the ratio is **1.25×** (range **0.90×–1.34×**); median plain wall time is about **0.073 ms**. Earlier captures on the same host had different ratios. Treat these very short intervals as timing diagnostics, not a stable overhead estimate.

The raw capture was refreshed against native build `a6aac84f41ed`; its established filename retains the preregistration date. Raw capture: [`substrate_conversation_runtime_access_trace_overhead_v1_20260925.json`](../../../evaluation/reports/substrate_conversation_runtime_access_trace_overhead_v1_20260925.json). Independent arithmetic analysis: [`analysis JSON`](../../../evaluation/reports/substrate_conversation_runtime_access_trace_overhead_v1_analysis_20260925.json). Runner and analyzer: [`runner`](../../../scripts/substrate_conversation_runtime_access_trace_overhead_v1.py), [`analyzer`](../../../scripts/analyze_substrate_conversation_runtime_access_trace_overhead_v1.py).

## Interpretation and limits

Tracing adds measurable work in the two-deliberation cell, but absolute closures are only tens of microseconds and the one-deliberation baseline includes a timing outlier. Treat these ratios as a plumbing diagnostic, not a stable performance estimate or a CPU-scale bound. This is one host and one small authored task family. It does not measure larger graph behavior, trace completeness, natural-task frame locality, or partitioned execution.

Next: exercise omitted trace paths (JIT predicate reads, aggregate/traversal Terms, and remaining effects), then derive candidate frame cuts and compare partitioned closure with monolithic closure and deliberately omitted-boundary controls.

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_conversation_runtime_access_trace_overhead_v1.py
python3 scripts/analyze_substrate_conversation_runtime_access_trace_overhead_v1.py
```
