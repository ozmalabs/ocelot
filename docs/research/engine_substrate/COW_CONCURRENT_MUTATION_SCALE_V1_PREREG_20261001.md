# Concurrent CoW topology and write-density v1 preregistration

**Question:** Do concurrent shared-snapshot isolation and allocator benefits persist across connected graph topologies and sparse versus denser branch-local edits, compared with eager copying?

## Design

- Native Rust workers use the same global `System` allocator meter and barrier lifecycle as the validated concurrent branch lifecycle probe.
- Cross topology `{path, star, grid}`, graph size `{10,000, 50,000}`, branch write density `{1%, 10%}`, concurrent fanout `{4, 16}`, and backend `{shared snapshot, eager copy}`. Three repetitions per backend cell; backend order is counterbalanced within each matched repetition.
- Base topologies are directed and deterministic: path successor edges, center-out star edges, or right/down rectangular-grid edges. Every node carries one initialized marker attribute; the topology determines degree and branch-index placement.
- Each worker forks one branch, inserts one uniquely typed branch node, updates the marker attribute on an evenly spread target set with an owned 128-byte payload, and adds one branch edge from each target to its branch node. All branches synchronize while live; half are cancelled/dropped; survivors are validated before release.
- A same-backend fork/drop/no-write wave and a thread-only wave calibrate allocator baselines. Record live requested bytes at baseline, all-live, after cancellation, and after drop; mutation-adjusted post-drop residual must be zero.

## Gates

1. Exact branch-added node-ID parity between shared snapshot and eager copy for every paired cell.
2. Updated attribute payloads and branch-edge counts match the independently constructed write schedule; primary and later snapshot fork preserve the complete original node/edge counts and marker values.
3. All surviving siblings retain all planned writes after half the branches are dropped.
4. Live allocation increases with branch activity; cancellation decreases it when half the branches are dropped; post-drop allocation equals the same-backend fork/drop control (adjusted residual exactly zero).
5. All 144 planned rows (3 topologies × 2 sizes × 2 write densities × 2 fanouts × 2 backends × 3 repetitions) complete, and capture hashes lock runner, analyzer, fixture, sources, and release binary.

## Measures and limits

Report full-wave wall time, all-live and post-cancellation allocator deltas, touched-node/edge counts, and the adjusted reclamation residual. Allocator counts are requested Rust bytes, not RSS/PSS or allocator metadata. Payloads and graph generation are synthetic; this is one-host systems evidence, not a natural workload distribution, general asymptotic bound, or serving benchmark.
