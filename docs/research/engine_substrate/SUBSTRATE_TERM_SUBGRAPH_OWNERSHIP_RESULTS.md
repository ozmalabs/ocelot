# Term subgraph ownership and cleanup results

**Status:** host-side ownership collector passes the three registered local cases. This is a prototype probe; the substrate's native `remove_node` behavior and API are unchanged.

## Evidence

The fixture materializes a four-node Term tree (`Cat` with a literal and a `Reverse(Var)` branch). Native `remove_node(root)` removes the root only and leaves the three descendants in all controls.

The diagnostic collector walks only `child.*` edges, identifies owned descendants with incoming graph references from outside the owned set, protects each such node and its child-descendant closure, then removes the remaining nodes deepest-first.

| Case | Native root-only removal | Collector result | Owner removed, later cleanup |
|---|---|---|---|
| No external reference | 3 Term nodes remain | Removes all 4 owned nodes; returns to 0-node baseline | Not applicable |
| Owner references `Reverse` subtree | 3 Term nodes remain | Removes root and unrelated literal; preserves `Reverse` and its `Var`, plus owner edge | Removes the retained 2-node subtree; returns to baseline |
| Owner references nested `Var` leaf | 3 Term nodes remain | Removes root, literal, and `Reverse`; preserves the `Var` and owner edge | Removes the retained leaf; returns to baseline |

Every retained subterm remains serializable with `term_subgraph_json`; every tested unowned Term node is removed; and removing the external owner permits exact return to the empty baseline. The whole probe passes all three cases.

## Scope and next work

This confirms a viable ownership-aware cleanup algorithm for fresh acyclic `child.*` term trees and explicit external references. It does not test cycles, concurrent graph mutation, native scheduler effects, or interaction with term-arena/interning lifetimes. The prototype lives only in the evaluation runner; callers still have only node-level `remove_node` and can continue to accumulate orphaned children. Next integrate an ownership-aware native operation (or a well-scoped shared helper), add regression tests for the three cases and malformed/cyclic inputs, and rerun the P4 retention curve with graph bytes and RSS. Do not replace ordinary `remove_node` with recursive behavior: that could delete shared graph data.

Protocol: [preregistration](SUBSTRATE_TERM_SUBGRAPH_OWNERSHIP_PREREG_20260925.md). Runner: [ownership probe](../../../scripts/substrate_term_subgraph_ownership.py). Lock: [frozen inputs](../../../evaluation/substrate_capability/term_subgraph_ownership_lock_20260925.json). Raw results: [JSON](../../../evaluation/reports/substrate_term_subgraph_ownership_20260925.json).
