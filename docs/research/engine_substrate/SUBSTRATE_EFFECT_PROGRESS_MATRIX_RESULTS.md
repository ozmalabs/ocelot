# Native effect progress matrix (2026-09-25)

## Result

A focused 17-case probe compared `run_rules` progress counts with serialized graph state for common structural and attribute effects. It covered edge insertion, duplicate edge insertion, edge-attribute replacement, edge deletion (present/absent), node creation/deletion, add-if-absent (new/existing), attribute writes (changed/identical), and `ReplaceValue` with a rewired trigger, additional incoming edge, or destination collision.

All five harness checks passed: every case settled under a terminal probe; every progressing case changed serialized state; every changed state reported progress; edge-attribute replacement counted as progress; and controlled no-op cases reported zero progress. The exact case records, final graphs, environment, native extension hash, source hashes, and harness hash are in the [raw report](../../../evaluation/reports/substrate_effect_progress_matrix_20260925.json). This is a small authored mechanism probe, not a broad workload or performance envelope.

## `ReplaceValue` collision rollback: fixed and measured

`ReplaceValue` snapshots and deletes each incoming edge to the old node, then inserts an edge to the new node with the old edge attributes. If the destination edge already exists, insertion replaces its attributes. The implementation now records the destination's old attributes in the existing `EdgeAttrsSet` undo step before insertion. A direct native `apply_rule_full`/`undo_apply` probe then passed for both a non-collision rewrite and a collision: source edges and attributes were restored, and the collided destination's original `value=99` was restored after the forward overwrite to `value=5`. The [raw report](../../../evaluation/reports/substrate_replace_value_undo_probe_20260925.json) records the case checks, command, toolchain, and hashes. The probe is direct mechanism evidence, not a property sweep across arbitrary effect sequences or Stage A scheduling.

## Follow-up

Extend rollback coverage to repeated/crossing replacements and attribute-bearing edge combinations, and determine whether a relevant Stage A path can exercise this effect safely. Expand the effect progress matrix to deferred rule edits, patches, concepts, and stale-node bindings; those effects are outside this run's coverage.
