# TypedGraph insert-phase profile v8 preregistration

Date: 2026-10-06

## Question

Does the small-graph insert slowdown seen in v7 come from
`TypedGraph::insert_node` (including index maintenance) or from the exact
post-insert `nodes_where` check that the v7 harness included in its timer?

## Workload and measures

Build a small Rust worker with the same four shard configurations (64, 128,
256, 512) and the same typed graph/index representation as v7. For 7,164 and
50,771 unique-value nodes, use three fresh worker processes per configuration
and size, with configuration order rotated. Each worker performs 41 fresh
branch insertions and separately times: shared graph fork, indexed
`insert_node`, exact indexed lookup for the new value, and `insert_node` on a
matched graph without the attribute index. Construct attributes outside all
timed regions. Check exact result and parent/sibling isolation outside timing.

## Analysis and gates

All measured insertions must allocate the expected NodeID, appear in the
branch's type order, and leave the parent indexed state unchanged. Report
medians per process and the median across the three processes; preserve sample
distributions. Compare indexed insertion with the no-index control and report
the lookup cost separately. This is a diagnostic microbenchmark; it does not
promote a production shard count or substitute for rule-closure/full-route
evaluation.
