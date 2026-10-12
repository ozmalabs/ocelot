# Reusable snapshot memory and reclamation v2 preregistration

Date: 2026-10-01

## Question

Does the storage-independent `Substrate.snapshot()` lifecycle preserve isolation while releasing branch and snapshot state on drop, and how do whole-process RSS/PSS deltas change across eager, shared-slab, and shared-graph-page implementations as the substrate grows?

## Frozen protocol

- Use the existing self-correction fixture builder with 0, 10,000, and 50,000 unrelated nodes added; retain the fixture's rule and candidate state but do not run prediction.
- Compare `full_copy`, `shared_slabs`, and `shared_graph_pages` through the private measurement hook that selects storage for a source-locked comparison. Application-facing code uses the same `snapshot().fork()` API.
- Run five measured fresh processes per size × backend, after one warmup, in a seeded randomized backend order (`20261001`).
- Sample Linux `/proc/self/smaps_rollup` at primary baseline, after snapshot capture, after branch fork, after one branch-local node insertion, after branch drop while the snapshot remains alive, and after the snapshot is dropped. Drop a verification fork separately before the final snapshot sample.
- Before and after mutation, verify the primary graph/rule revision and counts. Fork again from the retained snapshot after the candidate branch is dropped and verify that no branch-only node is visible. Record RSS, PSS, private/shared clean/dirty, and swap fields at every stage.

## Gates and reporting

All scheduled workers complete; source/native provenance is current; each worker verifies primary isolation, branch-local write visibility, later-fork visibility of the captured base, and successful drop lifecycle. Report every worker, the randomized schedule, and medians of stage-minus-baseline resident metrics. No PSS reclamation threshold is imposed because Linux allocator arenas and resident page accounting may retain memory after Rust objects are dropped. Treat post-drop deltas as observations, not direct live-heap measurements.

## Limits

One host, one synthetic self-correction substrate family, and no rule execution. `smaps_rollup` gives current process accounting, not kernel peak RSS or exact native allocations. This measures lifecycle and memory behavior, not concurrent readers, cancellation during active work, shared-prefix serving, candidate throughput, or natural-task generality.
