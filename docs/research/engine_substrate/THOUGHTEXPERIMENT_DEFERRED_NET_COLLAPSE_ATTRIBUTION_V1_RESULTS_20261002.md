# Thoughtexperiment deferred NetCollapse attribution v1 results

The source-locked panel passes all gates across three fresh workers. Each worker reaches the same fixed point in two passes with one progress step in the ordinary, attributed, and exact-snapshot reports. The deferred drain emits one `reflex_net_self_train_step` event per worker, marks it deferred, and its node targets cover the exact changed nodes and edges. The observation's consumed-status write is also represented. No events are dropped, and aggregate target sets contain all event targets.

This establishes producer-rule identity retention and target coverage for one queued NetCollapse fixture. It is not a training-quality or speed result. The fixture has one rule match and one queued collapse; it does not establish binding identity for multiple queued collapses, field/value provenance, causality under competing writers, or attribution for rule edits, rule patches, and framebuffer samples. Producer attribution also names the rule that enqueued the operation; it is not by itself a causal explanation of the resulting learned behavior.

The implementation path is source-linked at [`pending_net_collapses`](../../../runners/dsl/src/graph.rs), the [`Effect::NetCollapse` enqueue site](../../../runners/dsl/src/rewrite.rs), and [`apply_pending_net_collapses`](../../../runners/dsl/src/substrate.rs).

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_DEFERRED_NET_COLLAPSE_ATTRIBUTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deferred_net_collapse_attribution_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_net_collapse_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_net_collapse_attribution_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_deferred_net_collapse_attribution_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_deferred_net_collapse_attribution_v1_analysis_20261002.json)
