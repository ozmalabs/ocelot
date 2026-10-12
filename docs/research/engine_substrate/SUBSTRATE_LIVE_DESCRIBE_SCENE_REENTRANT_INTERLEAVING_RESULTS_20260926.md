# Live describe-scene reentrant interleaving results

Three fresh, source-stable workers pass the controlled same-thread reentrant test. A reaches `selected` and remains active while B enters the same `WorldAdapter`, receives a distinct Goal, completes selection/execution/result, and resolves/closes. A then resumes and completes its own lifecycle. The shared event order is exactly `instruction(A), selection(A), instruction(B), selection(B), execution(B), action_result(B), execution(A), action_result(A)` in every worker. Events, origin links, and Messages remain attached to their own Goal. Both replies match the baseline.

This demonstrates reentrant route behavior on one call stack. It is not evidence of thread safety; the separate [threaded probe](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_1_RESULTS_20260926.md) finds a repeatable PyO3 borrow failure under two actual threads.

- Preregistration: [`SUBSTRATE_LIVE_DESCRIBE_SCENE_REENTRANT_INTERLEAVING_PREREG_20260926.md`](SUBSTRATE_LIVE_DESCRIBE_SCENE_REENTRANT_INTERLEAVING_PREREG_20260926.md)
- Runner: [`substrate_live_describe_scene_reentrant_interleaving_v1.py`](../../../scripts/substrate_live_describe_scene_reentrant_interleaving_v1.py)
- Independent analyzer: [`analyze_substrate_live_describe_scene_reentrant_interleaving_v1.py`](../../../scripts/analyze_substrate_live_describe_scene_reentrant_interleaving_v1.py)
- Lock: [`live_describe_scene_reentrant_interleaving_v1_lock_20260926.json`](../../../evaluation/substrate_capability/live_describe_scene_reentrant_interleaving_v1_lock_20260926.json)
- Raw capture: [`substrate_live_describe_scene_reentrant_interleaving_v1_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_reentrant_interleaving_v1_20260926.json)
- Independent analysis: [`substrate_live_describe_scene_reentrant_interleaving_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_reentrant_interleaving_v1_analysis_20260926.json)
