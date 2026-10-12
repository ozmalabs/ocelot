# Scoped deferred-effect fallback — 2026-09-26

## Result

The amended v1.1 capture completed 18 fresh workers across 2/4/8 frame owners, two repeats, and three arms. All eleven independent gates pass. In all six `scoped_only` and `scoped_fallback` workers, the scoped call consumed one progress step, hit the locked one-step budget, and returned `deferred_effects_pending=true`.

The scoped-only control leaves every `PrevPercept.identity` and `CurPercept.identity` unset even though the writer trigger is marked done. This is the concrete failure mode: the scoped owner report names only the controller and is not a complete notification set while the deferred queue is pending. In each fallback arm, the caller sees the pending flag and invokes global closure. Its final identity assignments exactly match ordinary full closure for all six pairs, and an additional global closure is fixed-point/zero-progress. A separate cost sweep measures the settlement premium through 32 frame owners; see [fallback cost results](SUBSTRATE_SCOPED_DEFERRED_FALLBACK_COST_RESULTS_20260926.md).

At four percept pairs (eight frame owners), full and fallback closure assign `[4, 8, 12, 16]` to both previous and current percepts. Scoped-only assigns `null` throughout. This correctness probe did not preregister wall-time or memory measures; the separate cost study reports those measures for the same effect family.

## Interpretation and limits

This demonstrates one usable caller policy: if scoped settlement reports pending deferred effects or a progress-budget exit, abandon any assumption of complete scoped notifications and run global closure before consuming dependent state. It does not change the engine or implement fallback automatically. It tests only `TrackIdentity`, one synthetic graph shape, and exact identity projection; it does not prove that every deferred queue kind is surfaced, that all downstream derived state is covered by the subsequent global run in arbitrary orchestration, or that the fallback is affordable. The scoped API continues to report `frame_notifications_complete=false`.

## Reproducibility

- Protocol and v1.1/v1.2 amendments: [`SUBSTRATE_SCOPED_DEFERRED_FALLBACK_PREREG_20260926.md`](SUBSTRATE_SCOPED_DEFERRED_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_scoped_deferred_fallback_v1.py`](../../../scripts/substrate_scoped_deferred_fallback_v1.py)
- Independent analyzer: [`analyze_substrate_scoped_deferred_fallback_v1.py`](../../../scripts/analyze_substrate_scoped_deferred_fallback_v1.py)
- Initial v1 and v1.1 captures/locks are retained as exploratory. The accepted confirmatory lock is [`scoped_deferred_fallback_v1_2_lock_20260926.json`](../../../evaluation/substrate_capability/scoped_deferred_fallback_v1_2_lock_20260926.json).
- Initial raw capture, retained as exploratory after the first analyzer stopped on an absent global-report field: [`v1 raw`](../../../evaluation/reports/substrate_scoped_deferred_fallback_v1_20260926.json)
- Accepted v1.2 raw capture: [`substrate_scoped_deferred_fallback_v1_2_20260926.json`](../../../evaluation/reports/substrate_scoped_deferred_fallback_v1_2_20260926.json)
- Independent v1.2 analysis: [`substrate_scoped_deferred_fallback_v1_2_analysis_20260926.json`](../../../evaluation/reports/substrate_scoped_deferred_fallback_v1_2_analysis_20260926.json)

The v1.2 lock includes the runner, analyzer, protocol, native source, and build manifest hashes. Its analysis adds the scoped-only negative-control gate and confirms every hash. The v1 and v1.1 captures remain available for the harness history; only v1.2 is the confirmatory result.
