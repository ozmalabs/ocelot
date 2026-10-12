# Interacting tree closure scale v1 preregistration

Date: 2026-09-28

## Question

How does native fixed-point work vary with graph topology when two rules propagate a monotone state transition over the same attributed graph? Compare a balanced binary tree with a high-fanout star at 10k/100k/1M nodes, holding node/edge counts, rule logic, and initial state constant.

## Workload and oracle

Each fresh process builds N `TreeItem` nodes with attrs `status`, `ordinal`, `bucket=i mod 64`, and `depth`. Node 0 starts active; all others start pending. For balanced topology, parent(i)=floor((i−1)/2); for star topology, parent(i)=0. Every parent-child relation is stored in both directions (`child` and `parent`) to give each rule a single typed match edge. An attribute index on `(TreeItem,status)` supports exact final counts.

Two rules run to fixed point:

1. `activate_ready`: on `p -child→ x`, if p is active and x pending, set x to ready.
2. `commit_ready`: on `x -parent→ p`, if x is ready, set x active.

The independent oracle expects exactly N nodes, 2(N−1) edges, N active nodes, and zero pending/ready nodes. It also verifies sampled parent/child edges and immutable sample attrs. Audit-on/off are crossed as separate workers; each `(N,topology,replicate)` pair must match semantically. Three fresh-process replicates per cell yield 36 workers total. A seeded shuffled schedule varies execution order.

## Measurements and gates

- Stable full source/native lock at parent and every worker boundary; nonstale native build.
- Thirty-six unique workers: 3 sizes × 2 topologies × 2 audit modes × 3 replicates.
- Exact node/edge counts, fixed-point closure with zero progress overshoot, and exact indexed final-state counts.
- Audit-on/off semantic parity within each of 18 paired cells.
- For audit-on workers, per-rule candidate/effect counters conserve to global counters, clause candidate counts conserve to candidate tests, and unattributed candidate tests are zero.
- Record graph build, index, rule install, closure, and validation timings and RSS by stage; report audit-off closure as primary latency.
- Preserve all raw captures. Resource failure is a failed selected cell, not a reason to substitute a smaller N.

## Claim limits

This tests one binary-tree family, one star family, two authored monotone rules, and one initial state. It is not general closure complexity, arbitrary graph topology, nonmonotone update behavior, termination with fresh-name minting, or inference. Peak RSS includes an N-entry validation readback and must be separated from live post-closure RSS. Three sizes and three replicates do not establish an asymptotic law.
