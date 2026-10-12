# Live describe-scene threaded interleaving v1.1 results

## Result

All three fresh, source-stable workers reproduced the controlled overlap. Request A reached `selected` and remained active while thread B ran through its own selection, execution, and result events. B's events linked only to B's Goal; A's later events linked only to A's Goal. Both Goals resolved, closed, and left the active set; each retained three utterance subgoals.

The route still failed under concurrency. After B's lifecycle completed, its thread raised `RuntimeError: Already mutably borrowed` while `WorldAdapter.converse` read the MessageInterpretation node (`substrate/world_adapter.py:8082`, through `substrate_rs.Substrate.node`). A returned the baseline reply; B returned no reply. The same exception and stack location appeared in all three workers. This is a replicated capability limit for the tested concurrent call pattern, despite correct Goal/event identity.

## Source diagnosis

The PyO3 `Substrate` wraps the Rust core in `Arc<Mutex<SubstrateRs>>`, but the `run_rules` binding is declared with `&mut self` and calls `py.allow_threads` while executing a mutex-protected graph closure (`runners/dsl/src/py.rs`). The stack trace and borrow error suggest the PyO3 exclusive `PyClass` borrow conflicts with another thread entering `node` while a native call has released the GIL. This is a source-supported diagnosis, not a verified repair. Making only `run_rules` take `&self` may not suffice because concurrent mutating methods also borrow the PyClass mutably. A robust fix likely requires an API-wide interior-mutability/borrow audit or explicit serialization at the adapter boundary, followed by broad regression and latency measurement.

The native graph mutex serializes graph-core mutation, but that alone does not make the Python/PyO3 adapter surface concurrently callable.

## Evidence and limits

Independent analysis verifies the lock/hash, source stability, exact event order and owners, pause state, Goal terminal state, repeated traceback, and reply asymmetry. This is one controlled `describe_scene` call pattern across three fresh workers. It does not establish all thread schedules, all adapter operations, external-I/O safety, or concurrency scaling.

- Preregistration: [`SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_PREREG_20260926.md`](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_PREREG_20260926.md)
- v1.1 amendment: [`SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_live_describe_scene_threaded_interleaving_v1_1.py`](../../../scripts/substrate_live_describe_scene_threaded_interleaving_v1_1.py)
- Independent analyzer: [`analyze_substrate_live_describe_scene_threaded_interleaving_v1_1.py`](../../../scripts/analyze_substrate_live_describe_scene_threaded_interleaving_v1_1.py)
- Lock: [`live_describe_scene_threaded_interleaving_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_1_lock_20260926.json)
- Raw capture: [`substrate_live_describe_scene_threaded_interleaving_v1_1_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_1_20260926.json)
- Independent analysis: [`substrate_live_describe_scene_threaded_interleaving_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_1_analysis_20260926.json)
