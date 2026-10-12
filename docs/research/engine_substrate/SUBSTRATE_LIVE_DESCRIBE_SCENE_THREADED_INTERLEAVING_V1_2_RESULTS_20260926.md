# Live describe-scene threaded interleaving v1.2 results

## Result

The source-locked capture passed in three fresh worker processes. In each worker, request A paused after its selection event. The instrumented per-adapter lock observed request B attempting acquisition while A was paused; B emitted no selection event before A was released. After release, A completed its lifecycle and reply, then B completed its own lifecycle and reply. Event order was `instruction → selection → execution → action_result` for A followed by the same sequence for B. Goal/message/origin identity remained distinct, both Goals resolved and closed, both threads joined without errors, and both replies exactly matched the established describe-scene baseline.

The serialized capture confirms the route-specific RLock mitigation for this schedule. It does not repair the native PyO3 borrow boundary; it prevents this adapter route from entering that boundary concurrently. The capture records a median full-seed boot time of about 12.4 seconds, but does not measure turn latency with and without the guard. Thus full-turn overhead is unknown.

## Evidence and limits

- Amendment: [`SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_2_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_2_AMENDMENT_20260926.md)
- Runner: [`substrate_live_describe_scene_threaded_interleaving_v1_2.py`](../../../scripts/substrate_live_describe_scene_threaded_interleaving_v1_2.py)
- Independent analyzer: [`analyze_substrate_live_describe_scene_threaded_interleaving_v1_2.py`](../../../scripts/analyze_substrate_live_describe_scene_threaded_interleaving_v1_2.py)
- Lock: [`live_describe_scene_threaded_interleaving_v1_2_lock_20260926.json`](../../../evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_2_lock_20260926.json)
- Raw capture: [`substrate_live_describe_scene_threaded_interleaving_v1_2_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_2_20260926.json)
- Independent analysis: [`substrate_live_describe_scene_threaded_interleaving_v1_2_analysis_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_2_analysis_20260926.json)

Only one `describe_scene` schedule on one adapter was exercised. Other adapter methods, native entry points, routes, interleavings, shared lower-level objects, external effects, and scaling remain open. Same-thread reentry was confirmed by the prior v1 reentrant capture, but was not part of this v1.2 threaded schedule.
