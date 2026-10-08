# Conversation runtime access trace

**Run date:** 2026-09-25  
**Evidence grade:** authored workload trace with paired semantic control  
**Status:** Four traced/untraced pairs match progress and task projections. Instrumented site counts reconcile with per-rule scale-audit operation counts.

## Protocol and results

The runner [`substrate_conversation_runtime_access_trace_v1.py`](../../../scripts/substrate_conversation_runtime_access_trace_v1.py) exercises native `conversation_deliberation_phase4a` rules with one or two generated deliberations and two fresh graph replicates per size. Each input is run with tracing disabled and enabled. Both arms must select the supported answer, reject the repair alternative and unsupported candidate for the expected reasons, reach a fixed point, and produce identical projections and progress.

All seven runner checks and all independent analyzer checks pass. On the expanded trace build, the four traced cells contain 115 events each at size one and 230 each at size two, with no overflow; the added counts are concrete adjacency reads. Across the cells, every emitted resource key falls within its rule's static access projection. Per-rule event counts exactly reconcile at the measured sites: accepted pattern edges, Attr evaluations, SetAttr attempts, edge insertions, and node insertions. The traced rules induce 46 static possible writer-reader pairs and 14 concrete identity overlaps per replicate; 32 static pairs are simply unobserved in these finite runs.

Raw capture: [`substrate_conversation_runtime_access_trace_v1_20260925.json`](../../../evaluation/reports/substrate_conversation_runtime_access_trace_v1_20260925.json). Independent consistency analysis: [`analysis JSON`](../../../evaluation/reports/substrate_conversation_runtime_access_trace_v1_analysis_20260925.json).

## Interpretation and limits

This is a second authored rule family alongside CAN and supports the instrumentation's correctness on these selected sites. It does not establish complete runtime footprints, prove that unobserved dependencies are absent, estimate trace overhead, measure treewidth, or show that partitioned closure preserves monolithic closure. It is not evidence that the conversation workload is representative of natural tasks.

Next: measure trace overhead on this workload, extend coverage to omitted JIT/aggregate and effect paths, then derive candidate frame partitions from concrete identities and compare partitioned closure with monolithic closure plus deliberately omitted-boundary controls.

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_conversation_runtime_access_trace_v1.py
python3 scripts/analyze_substrate_conversation_runtime_access_trace_v1.py
```
