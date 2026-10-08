# Live dynamic helper work capture v1.4 results

Date: 2026-10-05  
Protocol: [v1.4 preregistration](SUBSTRATE_LIVE_HELPER_WORK_CAPTURE_V1_4_PREREG_20261005.md)  
Runner: [`substrate_live_helper_work_capture_v1_4.py`](../../../scripts/substrate_live_helper_work_capture_v1_4.py)  
Analyzer: [`analyze_live_helper_work_capture_v1_4.py`](../../../scripts/analyze_live_helper_work_capture_v1_4.py)

## Result

All preregistered capture and analyzer gates passed across three fresh worker processes and six requests. The native release extension was rebuilt with `scripts/engine_build.sh --lib-only` and passed engine provenance checks. All 2,394 observed RuleUID observations map to request-local post-request definitions; 401 distinct active rule definitions reproduce; final graph semantic digests, request access traces, and request work traces reproduce; semantic controls pass; and no trace events were dropped.

The live route entered three helper families, attributed to rule UIDs 303–305. Across three workers, each family was invoked once per worker:

| Helper | Population nodes enumerated | Node attributes counted | Parts parsed | Additional work |
|---|---:|---:|---:|---|
| ShapeDecode | 1,230 | 14,889 | 1,203 | 213 relation-cue nodes; 960 candidate-part scores |
| TransformDecode | 1,230 | 14,889 | 1,203 | 960 search-candidate loop units |
| DimInfer | 1,230 | 14,889 | 1,203 | 18 generator-population nodes |

Across all three helpers, the trace recorded 9 invocations and 54,117 internal work units (54,126 including the invocation markers). On this route, each invocation enumerated a 410-node codebook population, parsed 401 parts, and counted 4,963 attributes. The codebook population query is whole-graph for the declared type; these counts do not demonstrate a small frame boundary. The measurement also does not yet attribute nodes to learned frames.

Only ShapeDecode, TransformDecode, and DimInfer were called in this prompt pair. The other instrumented helper families remain unexercised by this capture. Candidate counters are explicitly loop units at selected sites, not a uniform unit of computational cost or a full count of all match candidates and rejected candidates.

## Baseline comparison and limits

A separate [post-hoc comparison](../../../evaluation/reports/live_helper_work_capture_v1_4_baseline_parity_20261005.json), computed from the v1.3 and v1.4 raw archives, found identical graph digests, task outcomes after removing process IDs/timing/source receipts, prompt/reply pairs, access rows, and all non-helper work rows. The helper events are the additional work rows. This supports output and observed-access parity for the selected route. It is not a preregistered paired latency experiment, and the trace does not establish instrumentation overhead.

The helper counters are attributed to RuleUID and operation but not to a frame identity. The v1.3 static manifest still marks zero rules as proven local; there is no natural-task prevalence estimate, separator-width result, complete matcher rejection trace, or exact-inference factor-interface measurement. The next gate is prospective frame attribution and paired instrumented/uninstrumented cost measurement across independently sampled tasks, then expansion to helper families not covered here.

## Artifacts

- [Raw three-worker capture](../../../evaluation/reports/substrate_live_helper_work_capture_v1_4_workers_raw_20261005.json.gz), compressed SHA-256 `bf8efe07b7be556a22a52c5d4f716fee8c4c25c1c1e02d3f80b4d5ea2a75f39e`.
- [Capture summary](../../../evaluation/reports/substrate_live_helper_work_capture_v1_4_20261005.json).
- [Independent work and rule analysis](../../../evaluation/reports/live_helper_work_capture_v1_4_analysis_20261005.json).
- [Baseline parity analysis](../../../evaluation/reports/live_helper_work_capture_v1_4_baseline_parity_20261005.json).
- [Source lock](../../../evaluation/substrate_capability/live_helper_work_capture_v1_4_lock_20261005.json), SHA-256 `35639486e13bae301de0841481a7c7d1d43fa64fe454d3545d48792c3daf0d23`.
