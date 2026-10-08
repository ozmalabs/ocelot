# Thoughtexperiment deferred RulePatch attribution v1 results

The multi-producer source-locked panel passes all gates across three fresh workers. Both `submit_alpha` and `submit_beta` queue the same patch node before drain. Deduplication is preserved: each worker records one deferred event with both producer names, commits the RulePatch once, and advances the target from revision 0 to revision 1. Ordinary, attributed, and exact-snapshot settlement agree at a two-pass fixed point with two progress steps. The patch receipt node is included in the trace, exact graph changes are covered, aggregate targets contain event targets, and no events are dropped.

The event's `rule_name` remains the first producer for legacy consumers; the new `origin_rules` array is the complete producer set. This is explicit multi-origin attribution, not proof that both producers were causally necessary or a choice of one true cause. The fixture covers one shared patch node, one successful CAS commit, and one host. It does not measure performance or autonomous self-repair.

The implementation is source-linked at [`pending_rule_patches`](../../../runners/dsl/src/graph.rs), the [`Effect::ApplyRulePatch` enqueue/dedup site](../../../runners/dsl/src/rewrite.rs), [`apply_pending_rule_patches`](../../../runners/dsl/src/substrate.rs), and the serialized [`origin_rules` event field](../../../runners/dsl/src/py.rs).

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_DEFERRED_RULE_PATCH_ATTRIBUTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_patch_attribution_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_patch_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_patch_attribution_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_deferred_rule_patch_attribution_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_deferred_rule_patch_attribution_v1_analysis_20261002.json)
