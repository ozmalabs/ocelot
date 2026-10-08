# Deferred RulePatch refusal and conflict fallback — 2026-09-26

## Result

The locked 36-worker matrix passed all ten independent gates across two cases, 1/2/4 frame outputs, two repeats, and `full`, `scoped_only`, and `scoped_fallback` arms. Every scoped arm hit the one-step budget and reported pending deferred work. All full/fallback arms reached fixed point, and a terminal closure made zero progress.

- **Stale at submission:** the patch's expected revision was 1 while the live rule remained at revision 0. Full and fallback both recorded `status=refused`, `reason=stale_revision`, and `result_revision=0`; the live rule stayed at revision 0 and all output flags stayed false.
- **Same-revision conflict:** two patches targeted revision 0 and the same content hash. In all six full/fallback pairs, the first inserted patch committed revision 1 with `reason=ok`; the second was refused with `reason=stale_revision` and `result_revision=1`. The updated `Lit(true)` rule then completed every output frame.

Fallback and full graph/rule projections match exactly in all 12 pairs. Scoped-only controls retain the pending patch nodes, leave revision 0, and do not complete any outputs.

## Interpretation and limits

The deferred queue preserves both successful commit and refusal receipts under the explicit global-closure fallback. A deterministic insertion-order commit/refusal sequence is observed for two patches on one target in this single-threaded fixture. This is not a guarantee about concurrent mutation, larger queues, or every caller's patch ordering. It does not test effects-field changes, protected targets, malformed patches, mixed deferred queues, cost, or automatic frame notifications.

## Reproducibility

- Protocol: [`SUBSTRATE_SCOPED_RULE_PATCH_CONFLICT_FALLBACK_PREREG_20260926.md`](SUBSTRATE_SCOPED_RULE_PATCH_CONFLICT_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_scoped_rule_patch_conflict_fallback_v1.py`](../../../scripts/substrate_scoped_rule_patch_conflict_fallback_v1.py)
- Independent analyzer: [`analyze_substrate_scoped_rule_patch_conflict_fallback_v1.py`](../../../scripts/analyze_substrate_scoped_rule_patch_conflict_fallback_v1.py)
- Source/build lock: [`scoped_rule_patch_conflict_fallback_lock_20260926.json`](../../../evaluation/substrate_capability/scoped_rule_patch_conflict_fallback_lock_20260926.json)
- Raw capture: [`substrate_scoped_rule_patch_conflict_fallback_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_rule_patch_conflict_fallback_v1_20260926.json)
- Independent analysis: [`substrate_scoped_rule_patch_conflict_fallback_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_scoped_rule_patch_conflict_fallback_v1_analysis_20260926.json)

All locked protocol, runner, analyzer, native source, binding, and build hashes match.
