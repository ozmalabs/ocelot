# Native typed-graph storage scale v1 preregistration

Date: 2026-09-28

## Question

What CPU time and process-memory envelope does the current Python-to-native substrate mutation path require to construct a sparse typed graph at 10k, 100k, and 1M nodes, and does indexed node/edge readback remain correct at sampled positions?

## Workload

Each fresh worker constructs one `Substrate` directly, without seed boot or rule installation. It inserts N empty-attribute `StorageProbe` nodes through `PySubstrate.add_node` and N−1 `next` edges in a directed chain through `add_edge_unchecked`, retaining only the previous/current node IDs. N is 10,000, 100,000, and 1,000,000; run two fresh processes per size in a deterministic shuffled schedule (six workers). It records process RSS before graph construction, after node construction, and after edge construction, plus peak RSS, CPU/wall time for node insertion, edge insertion, and total construction. It validates node/edge counts and reads the first, middle, and last nodes and the outgoing edge at sampled positions.

The primary size metrics are incremental RSS (`after − before`) and total construction CPU/wall time. A Python wrapper is used because it is the public mutation surface. Empty attrs and a single chain relation isolate core node/edge storage; they are not representative of full runtime facts, attributes, rule vectors, closures, or OS page cache.

## Provenance and admission gates

- Six unique worker processes; two workers at each size.
- Stable source/native lock at parent, worker start/end, and parent post-run.
- Exact N/N−1 graph counts and sampled endpoint/middle chain checks.
- Positive phase timings, nondecreasing RSS observations, and all raw worker records retained.
- Report both byte totals and per-node slopes; do not fit or claim an asymptotic law from three sizes.

## Claim limits

This measures storage construction and sampled reads only. It does not measure rule closure, inference, application workloads, deletion/reuse, fragmentation, concurrent access, allocator behavior after dropping graphs, or 10M–100M-node capacity. RSS deltas are process-level measurements and include runtime/import overhead. The benchmark must report failure or resource limits without replacing the selected sizes post hoc.
