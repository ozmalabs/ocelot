# Native scoped owner effect matrix — 2026-09-26

## Result

The amended, pre-locked 60-worker matrix passed all ten independent gates. Across five direct effect shapes at 2, 4, and 8 consumer frames, the scoped mutation report returned exactly the same owning Microtheories as the full before/after snapshot oracle in every paired run. Scoped node and edge targets covered all oracle targets; unrelated frame owners were absent. The writer settled without a progress cap or pending deferred effects, and a second scoped call made zero progress in all cells.

| Effect shape | Reported owners |
|---|---|
| Shared edge insertion | Controller and owners of both endpoints |
| Shared edge deletion | Controller and owners of both endpoints |
| Shared node attribute write | Controller and the node owner |
| Owned node birth | Controller, which acquires the new node |
| Owned node deletion | Controller and owners incident to the deleted node, including the other endpoint of its removed edge |

The paired graph outcomes match in every cell. The native extension identity is uniform across all 60 fresh workers. The full snapshot oracle is O(V+E) and is used only for correctness comparison, not as a timing baseline.

## Interpretation and limits

This extends the prior conversation `SetAttr` confirmation to edge insertion/deletion and node birth/deletion, including ownership-link lifecycle effects. It confirms conservative direct owner mapping for these authored graph mutations. It does not test deferred effects, rule/Term/concept-definition changes, arbitrary dependency discovery, automatic queue delivery, scheduler completeness, natural-task partitions, or performance. The scoped API still reports `frame_notifications_complete=false`; callers remain responsible for mapping and scheduling owners, and must not rely on its write set when `deferred_effects_pending` is true.

## Reproducibility

- Protocol with harness amendments: [`SUBSTRATE_NATIVE_SCOPED_OWNER_EFFECT_MATRIX_PREREG_20260926.md`](SUBSTRATE_NATIVE_SCOPED_OWNER_EFFECT_MATRIX_PREREG_20260926.md)
- Runner: [`substrate_native_scoped_owner_effect_matrix_v1.py`](../../../scripts/substrate_native_scoped_owner_effect_matrix_v1.py)
- Independent analyzer: [`analyze_substrate_native_scoped_owner_effect_matrix_v1.py`](../../../scripts/analyze_substrate_native_scoped_owner_effect_matrix_v1.py)
- Amended v1.2 lock: [`native_scoped_owner_effect_matrix_v1_2_lock_20260926.json`](../../../evaluation/substrate_capability/native_scoped_owner_effect_matrix_v1_2_lock_20260926.json)
- Original and v1.1 locks retained: [`initial lock`](../../../evaluation/substrate_capability/native_scoped_owner_effect_matrix_lock_20260926.json), [`v1.1 lock`](../../../evaluation/substrate_capability/native_scoped_owner_effect_matrix_amended_lock_20260926.json)
- Raw capture: [`substrate_native_scoped_owner_effect_matrix_v1_20260926.json`](../../../evaluation/reports/substrate_native_scoped_owner_effect_matrix_v1_20260926.json)
- Independent analysis: [`substrate_native_scoped_owner_effect_matrix_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_native_scoped_owner_effect_matrix_v1_analysis_20260926.json)

The first two launches stopped before a complete cell because the harness expected two optional status fields on the snapshot oracle; both failures and the amendments are recorded in the protocol. Neither produced an accepted capture. The accepted run used the frozen v1.2 lock, and every locked source/build hash matched in the analysis.
