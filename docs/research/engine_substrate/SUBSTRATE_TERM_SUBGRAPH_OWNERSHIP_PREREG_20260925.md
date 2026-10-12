# Reflected Term subgraph ownership and cleanup preregistration

**Question.** Can a child-edge traversal reclaim an unshared reflected Term tree while preserving a subtree or leaf held by an external graph node, and can the retained substructure be cleaned later when that owner is removed?

## Fixture and protocol

Use a fixed nested Term with a root, a literal sibling, and a nested Reverse/Var branch. In separate fresh native Substrates, probe (1) no external owner, (2) an external `TermOwner` edge to the nested Reverse subtree, and (3) an external owner edge to the nested Var leaf. Confirm first that native `remove_node(root)` leaves the child nodes. Then run a diagnostic host-side collector that traverses only `child.*` edges from the requested root, finds owned descendants with external incoming edges, marks each externally held node and its child-descendant closure as protected, and deletes unprotected nodes deepest-first. A root with an external owner is outside this protocol; none of the three controls uses that case.

For each case, record before/after IDs and types, removed/protected IDs, owner-edge survival, root and retained-subgraph JSON validity, and node counts. For shared cases, remove the owner only after validating preservation, invoke cleanup on the formerly owned subroot, and require the graph to return to its pre-materialization node count. The no-owner case must return exactly to baseline immediately.

## Gate and limits

The prototype passes only if unshared materialization is fully removed; external owners and their reachable Term subtrees survive intact; unrelated Term siblings are reclaimed; and later owner removal permits complete cleanup. This is a local algorithm probe, not a production API, concurrent-mutation algorithm, cyclic graph collector, full `WorldAdapter` workload result, or substitute for native regression tests. The engine's `remove_node` semantics remain unchanged.
