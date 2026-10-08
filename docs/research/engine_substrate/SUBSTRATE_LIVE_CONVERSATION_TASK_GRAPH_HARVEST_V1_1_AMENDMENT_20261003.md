# Live task-graph harvest v1.1 analyzer amendment

Date: 2026-10-03  
Status: post-capture analysis correction.  
Capture: [v1 locked compressed graph capture](../../../evaluation/reports/live_conversation_task_graph_harvest_v1_20261003.jsonl.gz)

The source-locked v1 runner completed all ten processes and retained all graph snapshots. The first independent analyzer failed before writing an analysis because its summary calculation referenced `statistics.median` without importing `statistics`. This is an analyzer-only defect; no worker, graph, source lock, or task output was changed. Preserve the first analyzer and lock. Analyzer v1.1 adds the missing import, writes a separate analysis artifact, and independently replays the full ownership, graph-digest, replicate, and route-contract checks from the compressed raw capture. The amendment analyzer hash is recorded in its analysis output; it is not represented as an input hash from the original capture lock.
