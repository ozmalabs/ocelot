# Mixed deferred-queue fallback — 2026-09-26

## Result

The locked 18-worker matrix passed all nine independent gates. It covers one, two, and four previous/current percept pairs (2/4/8 frame outputs), two fresh-process repeats, and `full`, `scoped_only`, and conditional `scoped_fallback` arms. One writer firing enqueues a CAS-valid RulePatch, a TrackIdentity operation over the percept populations, and a NetCollapse update; it also marks the writer and observation complete.

Every scoped arm stops after one progressing step and reports pending deferred work. In the fallback arm, global closure commits the rule patch at revision 1, assigns matching identities to every previous/current pair, updates the one-unit net to `W2=[[0.05]]` and `b2=[0.05]`, records the expected EMA surprise 0.15, and lets the newly enabled target rule set every output to complete. All six fallback states exactly match their ordinary-full counterparts. A terminal global closure is fixed-point/zero-work.

The scoped-only control marks the initiating observation consumed while leaving the patch pending, identities unset, weights zero, surprise zero, and all outputs incomplete. This shows that `deferred_effects_pending` is consequential across all three queue kinds even when the scoped caller's own graph writes have completed.

## Interpretation and limits

This is direct evidence that, for this simultaneous writer firing and these three queue types, a caller can safely abandon scoped completeness and recover the ordinary full-closure result with one global fallback. It tests the engine's combined between-pass drain order, graph receipt, identity assignment, numerical update, and downstream rule activation in one fixture. It does not establish arbitrary queue ordering, multiple writer firings, queue deduplication under complex overlap, framebuffer sampling, cost, or natural workload frequency. It does not change the API: notifications remain caller-driven and `frame_notifications_complete` remains false.

## Reproducibility

- Protocol: [`SUBSTRATE_MIXED_DEFERRED_QUEUE_FALLBACK_PREREG_20260926.md`](SUBSTRATE_MIXED_DEFERRED_QUEUE_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_mixed_deferred_queue_fallback_v1.py`](../../../scripts/substrate_mixed_deferred_queue_fallback_v1.py)
- Independent analyzer: [`analyze_substrate_mixed_deferred_queue_fallback_v1.py`](../../../scripts/analyze_substrate_mixed_deferred_queue_fallback_v1.py)
- Source/build lock: [`mixed_deferred_queue_fallback_lock_20260926.json`](../../../evaluation/substrate_capability/mixed_deferred_queue_fallback_lock_20260926.json)
- Raw capture: [`substrate_mixed_deferred_queue_fallback_v1_20260926.json`](../../../evaluation/reports/substrate_mixed_deferred_queue_fallback_v1_20260926.json)
- Independent analysis: [`substrate_mixed_deferred_queue_fallback_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_mixed_deferred_queue_fallback_v1_analysis_20260926.json)

Protocol, runner, analyzer, native rewrite/substrate/graph-rule/net-forward/term sources, binding, and native build manifest hashes match.
