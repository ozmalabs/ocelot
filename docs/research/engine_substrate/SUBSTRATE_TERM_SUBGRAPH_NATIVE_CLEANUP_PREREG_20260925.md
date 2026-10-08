# Native reflected Term subgraph cleanup preregistration

**Question.** Does the new native `remove_term_subgraph` operation reclaim unshared Term nodes, preserve externally referenced subtrees, and reject malformed/cyclic trees before mutation?

## Cases

Use a fixed four-node `Cat(Lit, Reverse(Var))` Term tree on fresh native Substrates. Run: unshared tree; external owner of a nested Reverse subtree; external owner of a Var leaf; external owner of the root; a child-edge cycle; a child edge to a non-Term node; non-Term root; and missing root. For external-reference cases, require target and owner edge to survive, then delete the owner and clean from the surviving Term subroot. For malformed/cyclic cases, require a typed error and byte-equivalent graph state before/after the attempted cleanup.

The production operation must preserve ordinary node-level `remove_node` semantics, delete only unprotected `child.*`-reachable Term nodes, and return removed/protected IDs. It must perform all traversal/type/cycle validation before deleting any node. Use the API through the rebuilt native Python extension; verify its content-based build record is current. This runner is an evaluation probe, not a pytest invocation.

## Gate and limits

Pass only if all eight cases meet their expected behavior, valid retained subterms round-trip through `term_subgraph_json`, owner removal permits complete cleanup, and all error cases leave the graph unchanged. This does not establish concurrent-mutation safety, arbitrary graph transactions, TermArena compaction, or P4 workload-level memory benefit. Normal `remove_node` remains node-only.
