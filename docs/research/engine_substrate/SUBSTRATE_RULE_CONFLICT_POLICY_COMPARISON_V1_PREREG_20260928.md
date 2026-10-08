# Rule conflict policy comparison v1

## Question

For the captured overlapping-write conflict, do existing rule `order` metadata or graph-resident proposal nodes provide a viable alternative to priority-by-registration? Can a narrow admission check reject the exact conflict before execution?

## Design

- Three fresh workers; each builds four independent cells: metadata-ordered conflicting writes under A→B and B→A insertion, and proposal-node representation under both insertion orders.
- The conflict is the same as the prior probe: identical trigger and stable-true predicate, A proposes value 1, B proposes value 2.
- Metadata cells set A `order=10`, B `order=20`, opposite to insertion order in the B→A cell; run the default global fixpoint with cycle detection.
- Proposal cells use `add_node_if_absent` to create one `ConflictProposal` node per rule with its rule/value attrs, linked from the target. Run with cycle detection and verify fixed point preserves both proposals.
- A pure runner-side exact-conflict admission predicate checks identical match/where and contradictory writes to the same variable/attribute. Record its rejection before rule installation. This is a feasibility prototype, not an engine feature.
- Capture source/native lock, termination report, graph projection, and callback counts.

## Gates

All workers replicate. Metadata-order cells should reveal whether default global execution honors `order`. Proposal-node cells must reach fixed point with both proposals preserved under either insertion order. The exact admission predicate must reject the synthetic conflict before runtime.

## Limits

The rejection prototype recognizes only exact identical matches/where Terms and direct same-key writes; it does not solve graph-pattern overlap or semantic predicate equivalence. Proposal nodes surface alternatives but do not choose a winner. This probe does not introduce any substrate behavior change.
