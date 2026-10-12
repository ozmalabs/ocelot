# Live runtime pre-request state capture v1 — results (2026-10-04)

## Result

The source-locked replicate-0/audit-on checkpoint run passes. The independent analyzer validates four complete primary graph/rule snapshots and confirms the post-request-one state is byte-semantically identical to the pre-request-two state after canonical serialization. Parent task projection, both replies, and final semantic graph digest all match the v1.6 capture.

| Boundary | Primary graph nodes | Primary graph edges | Primary rule slots |
|---|---:|---:|---:|
| Before request 1 | 24,892 | 11,129 | 2,357 |
| After request 1 | 25,039 | 11,471 | 2,363 |
| Before request 2 | 25,039 | 11,471 | 2,363 |
| After request 2 | 25,065 | 11,543 | 2,363 |

The primary store adds six rule slots during the first request; no additional primary rule slots appear during the second. The checkpoints preserve the full native graph and rule export at every boundary, not only node/edge totals. They are individually gzip-compressed and verified one at a time by the analyzer.

## Coverage limits

This confirms primary-state continuity and preserves replayable primary request-boundary states for this one authored route. Native global counter identities also include secondary stores; their full rule bodies and graphs are not exposed by the `WorldAdapter.inner` export API used here. The checkpoints therefore do not reproduce all global matcher work. This remains one host, one replicate, two prompts, and one selected route; it does not establish natural workload locality, termination, or broad tractability.

## Reproduction

- Preregistration: [protocol](SUBSTRATE_LIVE_RUNTIME_PRE_REQUEST_STATE_V1_PREREG_20261004.md)
- Runner: [checkpoint capture](../../../evaluation/substrate_capability/live_runtime_pre_request_state_v1.py)
- Independent analyzer: [checkpoint analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_pre_request_state_v1.py)
- Source lock: [locked inputs](../../../evaluation/substrate_capability/live_runtime_pre_request_state_v1_lock_20261004.json)
- Capture manifest: [request and checkpoint manifest](../../../evaluation/reports/live_runtime_pre_request_state_v1_20261004.json)
- Checkpoints: [compressed primary graph/rule states](../../../evaluation/reports/live_runtime_pre_request_state_v1_checkpoints/)
- Analysis: [independent analysis](../../../evaluation/reports/live_runtime_pre_request_state_v1_analysis_20261004.json)
- Parent comparison: [v1.6 results](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_6_RESULTS_20261004.md)

From the repository root, run `python3 evaluation/substrate_capability/live_runtime_pre_request_state_v1.py` followed by `python3 evaluation/substrate_capability/analyze_live_runtime_pre_request_state_v1.py`. The runner checks parent task-projection, reply, final-digest, request-boundary, and source-stability gates before reporting success.

## Next measurement

Extend native state export to enumerate each live store represented by the process-wide audit identities, or instrument store creation so full graph/rule bodies can be associated with store IDs at the time they are created. Then replay the primary and secondary store snapshots separately and compare per-store work with the global request totals. Keep any store whose state cannot be exported as an explicit coverage gap.
