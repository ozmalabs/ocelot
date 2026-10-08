# Active-rule node-deletion invalidation v1 results

**Evidence grade:** three fresh source-locked worker processes; all 7 runner gates and 8 independent analysis checks pass.

## Finding

Each worker builds two identical rule graphs. A rule matches `Root -trigger-> Target` and sets `Target.watched_count` to the count of `Root -watched-> *`. Both arms initially settle with count 1. Removing the `Doomed` node deletes the only watched edge, so an independent graph oracle reports zero.

In the default dirty mode, the subsequent engine call reports a fixed point with zero progress, performs zero rule enumerations/candidate pairs, and leaves `watched_count=1`. This is stale derived state. With `precise_dirty` enabled, deletion marks the watched-edge reader dirty: one rule enumeration and one candidate pair run, the target becomes 0, and closure reaches a fixed point. Median settlement wall times in this tiny fixture are 7.48 μs and 10.21 μs respectively; these are descriptive only.

The measured scope is one typed `Edges` reader and one public node deletion. The current default is explicitly `precise_dirty=false`, so the failure is relevant to ordinary operation unless callers enable the opt-in mode. This result does not cover all Term variants or mutation families. It exposes a deletion invalidation correctness gap; it is not evidence of tractability. See the [protocol](SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_delete_active_rule_invalidation_v1.py), [raw capture](../../../evaluation/reports/substrate_delete_active_rule_invalidation_v1_20260928.json), [analysis](../../../evaluation/reports/substrate_delete_active_rule_invalidation_v1_analysis_20260928.json), and [source lock](../../../evaluation/substrate_capability/delete_active_rule_invalidation_v1_lock_20260928.json).
