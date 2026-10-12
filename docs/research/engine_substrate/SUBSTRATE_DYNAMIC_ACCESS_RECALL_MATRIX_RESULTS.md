# Dynamic access recall matrix

**Run date:** 2026-09-25  
**Evidence grade:** selected mechanism probe  
**Status:** 17 of 18 supported-reader cases match a direct final-graph oracle; one effect-only attribute read remains stale by current scheduler policy.

## Protocol

The harness [`substrate_dynamic_access_recall_matrix.py`](../../../scripts/substrate_dynamic_access_recall_matrix.py) constructs isolated two-rule graphs. A reader binds through an unchanged `trigger` edge, derives an effect value from a graph query, and writes that value to a target. A writer then mutates one resource. The harness compares the reader's output with an independently computed oracle over the final graph and requires a subsequent `run_rules(1)` call to report no work.

There are 18 cases: seven query forms (typed `Edges`, `Neighbours`, `InNeighbours`, `ReachableFrom`, `MapNeighbours`, any-type `Edges`, and `Sum(Edges, EdgeAttr)`) under insertion and deletion (14); edge-weight replacement (1); effect-only node `Attr` read under node-attribute write (1); predicate `Attr` read under node-attribute write (1); and `NodesOfType` read under node birth (1). Each case also checks native `rule_access_sets()` for a reader/writer resource overlap.

## Result

The harness reports all 18 mutations visible, all 18 cases at a zero-work terminal probe, and native static access diagnostics available. All 18 pairs have a static resource overlap. Seventeen cases match their final-graph oracle. The only mismatch is `node_attr_read`: its observed value remains 0 while the final graph oracle is 7. The `node_attr_predicate_read` control refreshes to 7.

The extension was rebuilt from current source before the latest run, including the measured `AddEdge` attribute-replacement progress correction. The raw report at [`substrate_dynamic_access_recall_matrix_20260925.json`](../../../evaluation/reports/substrate_dynamic_access_recall_matrix_20260925.json) identifies commit `8bac3e90b39ca7eca12e88f856a9bc4b350add87`, the dirty-worktree state, native extension SHA-256 `558d13ddda7076ab087951f303dd7acf839025df608d97acecc808f4ed60e593`, and hashes for the harness, Rust sources, binding, and native build manifest. Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_dynamic_access_recall_matrix.py
```

## Interpretation and limits

`rule_access_sets()` correctly reports a dependency overlap for the failing case, but dependency presence does not mean every read is scheduled for replay. In `Substrate::dirty_by_writeset` (`runners/dsl/src/substrate.rs`), an attribute write re-wakes attribute consumers whose read is used in a `where` predicate; it suppresses re-wakeup for a rule with no `where` clause, where the attribute read only supplies an effect value. The source comment identifies duplicate effects, including minting and edge writes, as the reason for this policy. The predicate control demonstrates the narrower replay path works. Thus the matrix identifies a policy boundary, not a missing static access key.

This is behavioral coverage for controlled rule pairs, not a complete dynamic read trace, a proof for arbitrary rule bodies, a task-level frame-locality result, or a parallel execution test. The failing rule is potentially stale after a relevant node-attribute mutation. Whether it should replay depends on effect idempotence and replay semantics; broadening the wake policy without that analysis could duplicate non-idempotent effects.

## Next gate

Classify effect-only attribute readers by effect semantics. Start with controls for idempotent `set_attr`, additive/duplicate edge writes, deletion, and fresh-node minting; compare selective replay, current suppression, and full rescan against a monolithic oracle, including graph state, residual work, duplicate effects, and cost. Only then choose a safe scheduler rule or explicit effect idempotence contract. Follow this controlled gate with dynamic access traces and boundary perturbations on authored CAN and conversation workloads; retain full rescans as the correctness reference.
