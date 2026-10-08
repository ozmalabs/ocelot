# Describe-scene repeated-request identity results

## Result

All three source-stable fresh full-seed workers produced nonempty replies for two sequential `describe what you see` instructions against one attached three-percept scene. In every worker, the first request caused a `describe_scene` parent Goal to be minted. The second request minted no new parent; `_act_describe_scene` selected the same scene parent again. That Goal then comprehended both inbound Messages, while its `originated_in` edge list remained empty. The scene retained exactly one `described_by` parent. No selection, execution, result, or failure lifecycle events were emitted.

Thus route operation passes for both turns, while one-to-one Goal identity fails reproducibly. This is direct live evidence for sequential repeated use of this route, rather than an inference from the source audit. It does not establish behavior for concurrent calls or other action routes.

The independent analyzer verifies the raw capture and lock hashes, source stability at worker start/end and post-run, three distinct process IDs, nonempty replies, the repeated identity-failure structure, absence of Goal-bound lifecycle events, and a normalized graph shape replicated across workers. The runner's raw `observed_graph_shape_repeats` check is false because it compares full turn records including nondeterministic elapsed timings; this check is not used as evidence of graph divergence. The independent analyzer compares the structural projection with timings excluded and passes. The original raw capture is preserved without editing.

Median full-seed boot was 11.81 s; median turn time was 6.96 s. These timings include expensive lazy faculty construction and are descriptive for this setup only.

## Evidence

- Preregistration: [`SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md)
- Raw runner: [`substrate_describe_scene_repeated_request_identity_v1.py`](../../../scripts/substrate_describe_scene_repeated_request_identity_v1.py)
- Independent analyzer: [`analyze_substrate_describe_scene_repeated_request_identity_v1.py`](../../../scripts/analyze_substrate_describe_scene_repeated_request_identity_v1.py)
- Lock: [`describe_scene_repeated_request_identity_v1_lock_20260926.json`](../../../evaluation/substrate_capability/describe_scene_repeated_request_identity_v1_lock_20260926.json)
- Raw capture: [`substrate_describe_scene_repeated_request_identity_v1_20260926.json`](../../../evaluation/reports/substrate_describe_scene_repeated_request_identity_v1_20260926.json)
- Independent analysis: [`substrate_describe_scene_repeated_request_identity_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_describe_scene_repeated_request_identity_v1_analysis_20260926.json)
- Source audit: [`SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_PRODUCER_SOURCE_AUDIT_20260926.md`](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_PRODUCER_SOURCE_AUDIT_20260926.md)

## Next implementation gate

The parent Goal needs a request-scoped identity produced by the authored rule or an explicit host handoff, rather than a global “last scene Goal” scan. Each rule-minted utterance subgoal also needs an owner relation to that parent and a policy for whether lifecycle transitions apply to parent, children, or both. A follow-up should implement the smallest graph-native ownership mechanism, then test: repeated same-scene requests, distinct inbound-to-parent one-to-one mapping, child ownership, missing owner rejection, and full graph projection parity against the existing single-request behavior. Concurrent interleaving is a later gate after sequential ownership passes.
