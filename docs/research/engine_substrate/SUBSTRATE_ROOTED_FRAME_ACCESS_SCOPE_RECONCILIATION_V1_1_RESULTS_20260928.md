# Rooted-frame access-scope reconciliation v1.1 results

Date: 2026-09-28

## Scope isolation fixed

The v1.1 native trace carries a substrate graph identity in the rule scope and admits only events for the selected substrate. The direct negative control reproduces the old failure setup (enable an empty substrate's trace while a second populated substrate handles a request): it now returns zero foreign rows and zero drops without panic. In the corrected task capture the selected trace has 56,942 weighted rows for prompt 1 and 15,672 for prompt 2 per worker; the spurious UID 1 `edge:is_a` entries are gone. Three fresh workers pass source-lock stability, zero drops/count conservation, corrected trace parity, and semantic/task parity with the accepted v1.1 baseline. The independent analyzer confirms these gates and that all observed UIDs resolve.

## Remaining static dependency gap

Prompt 1 still has 20,122 weighted static-key mismatches, all associated with rule UID 303 (`sd_decode`): 50 `term_attr_read` resource keys, 2 `term_type_read` keys, and 2 `term_index_query` keys across 54 distinct rule/resource tuples. Prompt 2 has none. Static rows declare UID 303 reads `attr:codebook_epoch`, `attr:signature`, `attr:status`, and `edge:observed`, with `reads_any=false`; the rule's Term performs data-dependent ShapeDecode reads over codebook nodes. Inspection of `collect_term_reads()` shows that several high-level graph-reading Terms are conservatively marked `reads_any`, but `ShapeDecode` is omitted from that list. This is an actionable static declaration under-approximation, not the earlier trace contamination.

The analyzer reports 219 and 39 observed concrete dependency pairs for prompts 1 and 2, respectively, with none outside the declared static pair projection after trace scoping. This does not erase the static-key gap: its shared identities may still be absent from the candidate projection. Counter-conservation equations remain descriptive only and are not gates; their source semantics remain insufficiently aligned with trace event boundaries.

## Next gate

The registered `ShapeDecode` metadata repair and replay are complete in [v1.2 results](SUBSTRATE_ROOTED_FRAME_ACCESS_SCOPE_RECONCILIATION_V1_2_RESULTS_20260928.md): task semantics and corrected traces reproduce, the scope-isolation control passes, and observed static mismatches fall to zero. The next gate is broader source coverage for specialized Terms and a calibrated cost-accounting study before using access declarations as frame boundaries.

Artifacts: [v1.1 preregistration](SUBSTRATE_ROOTED_FRAME_ACCESS_SCOPE_RECONCILIATION_V1_1_PREREG_20260928.md), [runner](../../../scripts/substrate_rooted_frame_access_scope_reconciliation_v1_1.py), [independent analyzer](../../../scripts/analyze_rooted_frame_access_scope_reconciliation_v1_1.py), [lock](../../../evaluation/substrate_capability/rooted_frame_access_scope_reconciliation_v1_1_lock_20260928.json), [raw capture](../../../evaluation/reports/rooted_frame_access_scope_reconciliation_v1_1_20260928.json), [analysis](../../../evaluation/reports/rooted_frame_access_scope_reconciliation_v1_1_analysis_20260928.json).
