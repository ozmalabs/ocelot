# Pre-outcome task-frame capture v1 results

Date: 2026-10-05  
Status: capture-integrity gate passed; held-answer utility gate failed on one authored control family.

## Result

Three source-locked full-seed workers produced 21 pre-closure checkpoints across seven held-topic prompts. The capture lock remained stable, all checkpoints aligned with one post-checkpoint native access trace, and every trace had zero dropped rows and zero unmapped RuleUIDs. The independent analyzer reports `capture_integrity_pass=true` and `utility_gate_pass=false`.

Under the preregistered outcome-blind ingress ownership rule, frame sizes repeat exactly across all three workers: six nodes for “What is copper?” and nine nodes for each other prompt. The deterministic min-fill upper bound on each frame's induced **state graph** is 2. The cut has 8–10 crossing incidences to 5–7 distinct external nodes. These figures describe the protocol's message/mention/interpretation/discourse projection; they are not an inference primal width or factor interface.

| Prompt | Frame nodes | State-graph width upper bound | Crossing incidences | External boundary nodes | Native accesses after checkpoint | Distinct touched nodes outside cut |
|---|---:|---:|---:|---:|---:|---:|
| What do you know about copper? | 9 | 2 | 8 | 5 | 440,129 | 11,814 |
| What do you know about basalt? | 9 | 2 | 10 | 7 | 123,816 | 7,204 |
| What do you know about hexagon? | 9 | 2 | 10 | 7 | 131,397 | 7,242 |
| What is copper? | 6 | 2 | 10 | 7 | 138,583 | 7,279 |
| Can you tell me about copper? | 9 | 2 | 10 | 7 | 138,300 | 7,307 |
| What do you know about unobtainium? | 9 | 2 | 10 | 7 | 156,628 | 7,359 |
| What do you know about localhitium? | 9 | 2 | 10 | 7 | 166,542 | 7,403 |

Each row is identical across its three workers. Across 21 turns, native post-checkpoint trace rows count 3,886,185 access events in total (median 138,583 per turn; range 123,816–440,129). Every declared frame node is touched. The trace also touches 5–7 direct boundary nodes and 7,204–11,814 distinct nodes outside the cut per turn. The copper meta prompt is a high-work outlier at 440,129 events. Observed operations include large candidate/type-population and attribute/edge reads outside the projection. This demonstrates broad native graph access on this route; the trace is not a complete account of host-side reads and does not by itself say which accesses are semantically necessary.

The existing supported-answer checks pass for the copper meta/table, basalt, and hexagon prompts; unknown-topic refusal and injected local-source-hit checks also pass. All three “Can you tell me about copper?” turns return “What information should I use to answer that?” rather than the stored copper fact, so the positive held-answer release check fails on all three workers. Structural capture validity and answer utility are reported separately.

## Interpretation

This result does **not** validate the cheap-cut tractability hypothesis. It validates a reproducible way to declare a small input frame before native closure, while showing that a small input projection coexists with thousands of outside-cut nodes touched by the subsequent native rule trace. The observed cut and state-graph width therefore cannot stand in for the task's true factor interface. The high access counts also require separating genuinely necessary vocabulary/population work from avoidable global scans before attributing cost to the frame boundary.

The workload consists of seven authored held-topic prompts in one family, with three worker replicates. It is neither an independently sampled task population nor evidence about prevalence on natural workloads. It does not compare partitioned with monolithic closure, charge frame-discovery cost, or establish a speedup. Timing is omitted because graph snapshotting and runtime tracing add instrumentation overhead inside the measured conversation call.

## Artifacts

- [Preregistration](SUBSTRATE_PREOUTCOME_TASK_FRAME_CAPTURE_V1_PREREG_20261005.md)
- [Runner](../../../scripts/substrate_preoutcome_task_frame_capture_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_preoutcome_task_frame_capture_v1.py)
- [Source lock](../../../evaluation/substrate_capability/preoutcome_task_frame_capture_v1_20261005_lock.json)
- [Compressed raw capture](../../../evaluation/reports/preoutcome_task_frame_capture_v1_20261005/capture.json.gz)
- [Analysis](../../../evaluation/reports/preoutcome_task_frame_capture_v1_analysis_20261005.json)

## Next gate

Keep this operational frame definition fixed while sampling additional task families prospectively. Add an independent task-sampling frame and negative/positive locality controls; measure rule read/write dependencies, inference factor scopes and domains where applicable, host-side scans, frame-discovery cost, and task-result parity. Do not promote a general locality or tractability claim until observed access paths are reconciled with complete dependencies and repeated across independently authored families.
