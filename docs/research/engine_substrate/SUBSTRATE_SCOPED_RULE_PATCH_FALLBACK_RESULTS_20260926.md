# Scoped graph-native RulePatch fallback — 2026-09-26

## Result

The locked 18-worker experiment passed all ten independent gates across 1/2/4 output frames, two fresh-process repeats, and `full`, `scoped_only`, and `scoped_fallback` arms. Every scoped arm hit the one-progress-step budget and reported pending deferred work.

In every full and fallback arm, the queued CAS transaction committed with status `committed`, reason `ok`, and revision 1. The live rule's revision and content hash advanced, and the newly enabled rule set `done=true` on every frame output. All six paired fallback states exactly match ordinary full closure. The scoped-only control retains the pending patch, leaves target revision 0, and leaves all outputs incomplete.

This is a stronger deferred-effect confirmation than graph-value parity alone: fallback drains the rule-patch queue, mutates the active runtime rule, writes a durable graph receipt, then reaches downstream frame-owned state with the new rule body.

## Interpretation and limits

The tested policy is simple and explicit: when scoped reporting says deferred work remains (or the scope hits its budget), abandon any completeness assumption and run global closure before consuming dependent state. The result covers one successful `where`-field RulePatch against a unique unprotected target. It does not measure stale/refused patches, multiple competing patches, effects-field replacement, concurrent updates, cost, other deferred families, or arbitrary caller behavior. It proves no automatic owner notification; `frame_notifications_complete` remains false.

## Reproducibility

- Protocol: [`SUBSTRATE_SCOPED_RULE_PATCH_FALLBACK_PREREG_20260926.md`](SUBSTRATE_SCOPED_RULE_PATCH_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_scoped_rule_patch_fallback_v1.py`](../../../scripts/substrate_scoped_rule_patch_fallback_v1.py)
- Independent analyzer: [`analyze_substrate_scoped_rule_patch_fallback_v1.py`](../../../scripts/analyze_substrate_scoped_rule_patch_fallback_v1.py)
- Source/build lock: [`scoped_rule_patch_fallback_lock_20260926.json`](../../../evaluation/substrate_capability/scoped_rule_patch_fallback_lock_20260926.json)
- Raw capture: [`substrate_scoped_rule_patch_fallback_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_rule_patch_fallback_v1_20260926.json)
- Independent analysis: [`substrate_scoped_rule_patch_fallback_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_scoped_rule_patch_fallback_v1_analysis_20260926.json)

Protocol, runner, analyzer, native rewrite/substrate/graph-rule sources, PyO3 binding, and native build manifest hashes match the lock.
