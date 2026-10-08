# Adaptive high-degree edge index scale extension v1.3

**Question:** after the v1.2 semantic and 1M replay gates pass, can the same native builder construct and close a 10M-node high-fanout star within a bounded practical envelope?

## Workload and gates

Run three fresh processes at N=10,000,000 on the star topology with audit instrumentation off, using the exact v1 tree-closure worker and rules. Each graph has N attributed nodes, 2(N−1) directed typed edges, a root with N−1 children, and the same `pending → ready → active` propagation. Require exact node/edge counts, fixed-point status, zero overshoot, all nodes active, no pending/ready nodes, and correct sampled parent/attributes. Capture node-build, edge-build, closure, validation, live RSS phase points, and process peak separately. Each worker's source fingerprint must match the complete parent lock on all worker paths and native binary identity; pre/post locks must be stable.

## Reporting

Compare the 10M medians descriptively to v1.2's three 1M-star workers and the original pre-index 1M-star capture. Report full phase timings and memory. A successful 10M run only establishes this exact high-fanout monotone fixture on this host; it does not generalize to arbitrary rules or prove polynomial behavior. Do not run audit-on at 10M in this extension: its measured instrumentation multiplies candidate work and is not needed for the uninstrumented scale claim.

The preceding 10M pilot completed but its large JSON row was not retained by the command interface; it is treated as an unscored setup check. This extension uses new worker processes, raw paths, and an independent analyzer.
