# Scoped/full snapshot drain with cross-binding where invalidation v6 results

Date: 2026-10-01

## Result

The source/native-locked 27-worker factorial passes **300/300 checks** over R={1,8,32}, M={1,4,16}, with three fresh processes per cell. Every `JoinMiddle` starts with `eligible=true`, and the writer requires `eligible == true` in its where clause. For M=4/16, each binding's first effect sets its successor's `eligible=false` and then deletes that successor's unique match-driver edge. Despite this, all R×M snapshotted bindings produce their handled and verifier outputs in direct full closure, scoped-only, and scoped-plus-fallback. Final eligible-middle count is zero. This shows that these paths use the pre-mutation binding snapshot rather than rechecking the where predicate for each later binding.

Direct full closure and scoped-plus-fallback produce equal canonical node/edge facts in 27/27 workers, and the one-shot continuation selects the same NodeID in 27/27. Exact graph dictionaries match in 9/27 workers; insertion/serialization order remains distinct from semantic fact parity. All five deferred queue totals, fallback drains, and operation-work traces reconcile. Source and native fingerprints remain stable.

## Interpretation and limits

This is a targeted result for an attribute `Eq` where-clause and cyclic relation. M=1 is a single-binding control. It does not cover arbitrary nested conditions, external callbacks, node deletion, cross-frame writes, or natural-task frequency, and it does not prove general scope equivalence or complexity bounds. It provides direct evidence about the intended snapshot semantics under one predicate-invalidation pattern.

See [preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V6_PREREG_20261001.md), [runner](../../../scripts/substrate_all_queue_scoped_fallback_v6.py), [analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v6.py), [lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v6_lock_20261001.json), [worker capture](../../../evaluation/reports/all_queue_scoped_fallback_v6_workers_20261001.json), and [analysis](../../../evaluation/reports/all_queue_scoped_fallback_v6_analysis_20261001.json).
