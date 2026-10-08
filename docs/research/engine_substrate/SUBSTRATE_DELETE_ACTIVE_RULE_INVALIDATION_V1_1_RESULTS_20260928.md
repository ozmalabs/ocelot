# Active-rule node-deletion invalidation v1.1 results

**Evidence grade:** post-fix source-locked three-worker replay; all 8 runner gates and 8 independent analysis checks pass.

The engine now snapshots incident edge types during `remove_node` in both dirty modes, marks rules reading those types dirty, and invalidates affected incremental cursors. Precise mode still separately controls node type/attribute invalidation. The v1 pre-fix capture is retained and documents the original default-mode stale value.

In v1.1, default and `precise_dirty` conditions both begin at fixed point with `watched_count=1`. Deleting the sole `watched` edge makes the independent graph count zero. Both conditions re-enumerate one reader rule, test one candidate pair, update the value to zero, and report a fixed point. Median post-delete settle time is 12.86 μs for default and 11.91 μs for precise mode in this tiny fixture; timing is descriptive and does not imply a speed difference.

This verifies the direct typed `Edges` reader counterexample after the fix. It does not yet cover where-only negation readers, other Term variants, batches spanning many edge types, high rule counts, or general mutation-log parity. Continue with those controls before claiming deletion invalidation completeness.

Artifacts: [v1 preregistration](SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_PREREG_20260928.md), [v1.1 amendment](SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_1_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_delete_active_rule_invalidation_v1.py), [raw replay](../../../evaluation/reports/substrate_delete_active_rule_invalidation_v1_1_20260928.json), [independent analysis](../../../evaluation/reports/substrate_delete_active_rule_invalidation_v1_1_analysis_20260928.json), [source lock](../../../evaluation/substrate_capability/delete_active_rule_invalidation_v1_1_lock_20260928.json), [pre-fix counterexample](../../../evaluation/reports/substrate_delete_active_rule_invalidation_v1_pre_fix_20260928.json).
