# Effect-only attribute replay safety probe

**Run date:** 2026-09-25  
**Evidence grade:** selected mechanism probe  
**Status:** replay behavior differs by effect class; unconditional replay is unsafe for fresh-node minting. The edge-replacement progress undercount found in the initial run is corrected and remeasured in the current native build.

## Protocol

[`substrate_effect_only_attr_replay_safety.py`](../../../scripts/substrate_effect_only_attr_replay_safety.py) builds readers whose effects consume `Attr(x, watched)`. It runs normal closure, controlled `force_all_dirty()` rescans, a six-permutation shared-source competing-writer sweep at one binding, an independent-writer sweep at 2, 4, 8, 16, and 32 reader bindings, and false-predicate output-withdrawal cases with and without an explicit delete. Effects tested include `set_attr`, `add_edge` with a value attribute, and fresh `add_node`, including mixed effects. Stage A compare mode is enabled so eligible rule drains run through the engine's actual derive/`undo_apply`/commit comparison path. Two fresh-process runs produced byte-identical raw JSON (SHA-256 `9e8d8ec56e3642b73702023310441751a722c8a88af4ee35ca1c0e7b13cd1484`). The raw report preserves full graph snapshots, progress and compare-mode counters, terminal probes, native binary, source, and build-manifest hashes: [`substrate_effect_only_attr_replay_safety_20260925.json`](../../../evaluation/reports/substrate_effect_only_attr_replay_safety_20260925.json).

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_effect_only_attr_replay_safety.py
```

## Findings

Normal suppression leaves all three reader outputs based on the old value 0 after the source attribute is 7. The full rescan behaves differently by effect:

| Reader effect | After suppression | After full rescan | Interpretation |
|---|---|---|---|
| `set_attr(y, observed, Attr(x, watched))` | `observed=0` | `observed=7` | Correct single-value output; idempotent in this controlled case. |
| `add_edge(x, derived, y, {value: Attr(x, watched)})` | one edge with `value=0` | one edge with `value=7` | Existing edge is updated in place; no duplicate edge. In the initial run, the graph changed while `run_rules` reported zero progressing firings. |
| `add_node(born, ReplayBorn, {value: Attr(x, watched)})` | one node with `value=0` | two nodes with values `[0, 7]` | Replay mints a duplicate and retains the stale original. Unconditional replay is unsafe for this effect. |

The two-binding edge case starts with two roots and two derived edges; only the first root changes from 0 to 7. Suppression leaves edge values `[0, 0]`; full rescan yields `[7, 0]` with the derived-edge count unchanged at 2. Stage A compare records two drains with zero divergence and zero unsoundness. This is evidence that edge-attribute undo and replay preserve both the changed and unaffected binding in this specific pattern.

The two-binding mixed-effect case adds both `set_attr(y, observed, Attr(x, watched))` and the derived-edge update to one reader rule. Suppression leaves both output vectors stale (`observed=[0, 0]`, edge values `[0, 0]`); full rescan refreshes both to `[7, 0]` without adding edges. Stage A compare records zero drains for this rule shape, so this case has graph-oracle evidence but no derive/undo/commit comparison evidence.

The edge-plus-mint case combines `EdgeAttrsSet` with fresh `add_node` effects across two bindings. Rescan updates edge values from `[0, 0]` to `[7, 0]` and grows minted values from `[0, 0]` to `[0, 0, 7, 0]`. Stage A compare records two drains with no divergence or unsoundness. This exercises rollback of a mixed edge replacement and fresh mint together; it also makes the duplication cost of replaying a mint visible.

Rule order changes the terminal result under current suppression. In all six permutations of one reader and two writers (setting the same source attribute to 3 and 7), four settle with a reader output different from the final source attribute; the two permutations with the reader last match. The input nodes and update edges are identical across permutations. This confirms that effect-only attribute consumers can make the chosen fixed point depend on rule order even when every schedule reports a settled state.

The expanded binding sweep uses two roots with independent writers setting their attributes to 3 and 7; additional roots have no writer and should remain at 0. At each size 2, 4, 8, 16, and 32, four of six rule orders settle with at least one stale reader output; the two reader-last orders match the final-graph oracle. The mismatch counts by order are `[2, 2, 1, 0, 1, 0]` at every size, so the number of stale values per bad schedule stays bounded by two while its fraction falls with binding count. The probability of any stale output under a uniform choice among these six orders remains 4/6 for this generator. These are measurements of this fixed two-writer generator, not a general scaling law.

The withdrawal case uses a `where Attr(x, enabled) > 0` guard to add a derived edge, then sets `enabled=0`. The guard is false, but its previously added edge remains. A forced full rescan also retains it; the graph has one derived edge while the active-predicate oracle expects zero. This measures a boundary of the current effect model: a rescan that finds no matching binding does not itself retract past effects. This is not necessarily a defect if effects are intentionally monotonic; nonmonotonic tasks need explicit delete effects or a truth-maintenance mechanism.

An explicit retraction control pairs the same guard change with `del_edge(x, derived, y)` in the disabling rule. Both rule orders end with `enabled=0`, zero derived edges, and a zero-work terminal probe. This demonstrates that authored explicit deletion works in the controlled case and order pair; it does not provide automatic support tracking when a fact loses its justification.

### Current-source deletion contract

Source inspection aligns with these observations. Native [`EdgeData`](../../../runners/dsl/src/graph.rs) stores only `(src, edge_type, tgt)`; edge attributes are a separate value store, with no rule producer or justification recorded. [`Effect::AddEdge` and `Effect::DelEdge`](../../../runners/dsl/src/rewrite.rs) insert/replace or delete an edge at that structural key. `DelEdge` only acts when an executing binding reaches that effect; its undo record exists for rollback, not ongoing support tracking. The rule closure path therefore provides explicit graph effects, not truth maintenance: losing a match/guard does not reverse prior effects. For monotonic workloads, this is a valid forward-chaining contract. For nonmonotonic workloads, callers must author explicit deletion/replacement or use an external support-maintenance layer. This is a source-derived scope statement for the inspected native graph/rule path, not a claim about every host-side domain adapter.

All forty-six probe cases reach a subsequent zero-work terminal probe. The experiment supports the scheduler’s concern about fresh-node effects. It also shows that “attribute read used only in an effect” is too coarse a replay-safety category: replaying an attribute write is harmless here, and replaying an edge effect updates one existing edge, while fresh-node minting duplicates state. The initial probe exposed a progress-accounting defect: `TypedGraph::insert_edge` overwrites attributes on an existing `(src, type, tgt)` edge, while `apply_rule_full` credited only new edge insertion. The implementation now detects changed edge attributes, reports progress, records old attrs in `UndoStep::EdgeAttrsSet`, and preserves the update in Stage A forward-delta capture. With Stage A compare mode active, the single-binding edge-replacement and mint, two-binding edge-only in both orders, and edge-plus-mint cases each record two compared drains, zero divergent drains, and zero unsound drains. This exercises the actual derive/undo/commit consumer and supports rollback correctness for `EdgeAttrsSet` in these bounded patterns. The single-binding `set_attr` and the two-binding `set_attr` plus edge case record zero compare drains, so they have no Stage A rollback evidence.

## Limits and next gate

This is a controlled mechanism probe using `force_all_dirty`; compare mode is diagnostic and not a recommendation to enable full rescans. It covers a one-binding shared-source writer family and a fixed independent-writer family through 32 reader bindings, selected effect combinations, explicit/implicit withdrawal cases, and six permutations at each size. It does not establish behavior across arbitrary binding sets, larger order spaces, cycles, concurrent frames, or authored task workloads. Stage A compare mode only yields evidence for rules admitted by its derivability filter; the `set_attr` plus edge reader was not compared in this run. The edge case relies on the current graph’s edge upsert behavior and must not be generalized to other edge identities or mutation APIs.

Next, find an admitted form that compares the `set_attr` plus edge effect, vary writer count/value patterns and binding counts beyond 32, and make the explicit-deletion/no-truth-maintenance contract visible at the rule API boundary. Classify rule effects compositionally. A candidate selective-replay contract must establish: (1) which effects are idempotent for the same binding, (2) whether replay requires undo/replace of prior outputs to remove stale results, (3) whether every graph change is counted as progress, and (4) equivalence to full recomputation on bounded reference graphs. Until those conditions are met, keep current suppression and report its order-dependent stale-output boundary.
