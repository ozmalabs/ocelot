# Live task graph variance forensic replay v2

Date: 2026-09-27 local

## Result

Six exploratory fresh-process runs reused the v1.3 live `describe_scene` worker and captured its final graph. Worker start/end inputs and post-run inputs matched. All six runs reproduced 25,170 nodes, 11,809 edges, the same semantic graph digest, B message/origin IDs 25120/25126, and candidate totals A=677,795, B=842,748.

Raw graph diffs between runs contained four changed nodes (IDs 25147, 25151, 25162, 25165), all `SystemModel` nodes. Only `runtime_s` and `ts` differed. No node or edge count, semantic graph, or matcher-work differences occurred in these six runs.

The earlier v1.3 confirmatory capture had one lower-work worker among three (A=584,723; B=710,583), with two fewer nodes and three fewer edges and B message/origin IDs 25118/25124. Combining the samples gives the lower-work state in 1/9 workers; the follow-up six did not reproduce it. The v1.3 and forensic-v2 Python source closures, native extension, build manifest, worker script, protocol, and commit match. The amendment hash differs only because it now contains the post-capture analyzer-only correction disclosed in the v1.3 result. Thus the earlier outlier remains a real observation under the same measured implementation, but its exact differing node/edge records were not captured and its cause is unresolved. Do not replace the v1.3 range with a deterministic point estimate.

## Interpretation

The replay rules out persistent semantic or counter drift in the six follow-up workers and confirms that ordinary raw-graph differences from `SystemModel` timing fields are removed by the semantic digest. It does not explain the one earlier outlier or establish its frequency. Future confirmatory workers should retain compact typed node/edge delta summaries when semantic digest or candidate totals differ.

## Artifact

[Six-worker forensic capture and exact structural diffs](../../../evaluation/reports/substrate_live_task_graph_variance_v2_20260927.json), produced by the [diagnostic runner](../../../scripts/diagnose_substrate_live_task_graph_variance_v2.py). This is an exploratory variance follow-up, not a new confirmatory cost estimate.
