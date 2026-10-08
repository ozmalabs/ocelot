# TypedGraph attribute-index lifecycle v1 preregistration

## Question

Does the current TypedGraph attribute index pay for its build and lifecycle cost under repeated selective lookup, and what costs does it add to mutation, thought-experiment graph fork, and graph persistence restore?

This is an engine mechanism benchmark. It does not test automatic frame discovery, natural-task prevalence, or full Substrate fork cost.

## Protocol

The source-locked Rust probe builds deterministic graphs with 1,000, 10,000, and 50,000 typed nodes. An integer attribute has cardinality 8, 128, or 1,024, giving query selectivity near 12.5%, 0.78%, and 0.10%. For each cell it records index declaration/backfill; batches of 25 indexed and full-scan queries over seven samples; an equal mutation schedule on indexed and unindexed copies; indexed and unindexed `clone_sharing_graph_pages` costs; graph JSON serialization and restore; and restore-time index re-declaration/backfill.

The query control scans every node of the requested type and compares the same attribute value. Mutation changes the first `min(max(n/100,1),1000)` nodes to a fresh attribute value. Correctness gates require exact result IDs before mutation, exact query parity after mutation, exact serialized-graph equality after restore, and exact indexed result IDs after index re-declaration. The capture stores hashes for the runner, native probe, graph and persistence implementation, CoW containers, crate manifest, lockfile, and binary.

## Analysis rules

- Report raw per-cell values and ratios; do not infer a general speedup from this deterministic distribution.
- Estimate lookup break-even as index build/backfill cost divided by per-batch scan-minus-index savings, only where the denominator is positive.
- Treat index maintenance and fork time as index taxes; report these alongside query savings.
- Treat restore and re-declaration as separate costs because graph serialization intentionally omits derived-index declarations.
- A cell with any parity failure invalidates its timing comparison.
- One host, fixed modulo distribution, and graph-level forks limit the claim. No allocator/RSS measurement or full Substrate fork is included.

## Advancement gate

The benchmark can advance the index-admission design only if the capture is source-locked, every parity gate passes, and repeated query savings are reported against build, mutation, fork, and restore costs at all tested sizes/selectivities. An observed break-even in this panel motivates workload-mix evaluation; it does not authorize default index admission or establish tractability on natural tasks.
