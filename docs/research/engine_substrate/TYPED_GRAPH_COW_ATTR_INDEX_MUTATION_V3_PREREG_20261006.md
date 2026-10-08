# TypedGraph attribute-index COW mutation v3 preregistration

Date: 2026-10-06

## Question

Does the double-sharded COW attribute index preserve exact mutation semantics and improve branch fork-plus-first-write cost against an eager graph-copy control?

## Workload and arms

Build an indexed graph with N = 7,164, 16,384, and 50,771 typed nodes, a unique integer value per node, and one `(Concept, name)` index. Use 21 fresh in-process repetitions per size. For each operation, fork a fresh shared-pages branch or eager-copy branch before timing the mutation. Operations are: update one indexed value, insert a typed node carrying a fresh indexed value, delete an indexed node, and retype an indexed node to an unindexed type. Measure fork and first mutation separately with tracing disabled.

After each operation, compare the affected branch against its pre-operation state and require the primary and a sibling branch to retain the original index result. Require the mutation branch to show the correct new/removed/type-filtered result. Verify all original index queries before starting. Record each raw timing, each semantic gate, source and binary hashes, and build provenance. Report medians and paired ratios by size and mutation; do not aggregate across mutation types.

## Gate and limits

All source locks and semantic checks must pass. A per-index COW win requires shared fork-plus-write to improve on eager fork-plus-write without parent/sibling leakage. This is a graph-level synthetic gate: no Substrate closure, natural task, allocator byte count, concurrent branch, or general tractability claim follows. Any operation that traverses all indexed values (such as retyping/removal) may legitimately pay population-dependent cost; report it separately.
