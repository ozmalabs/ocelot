# Thoughtexperiment targeted commit factorial v1.1 — preregistration

**Date:** 2026-10-01  
**Question:** How does targeted residual commit cost vary independently with semantic node count, background edge density, and deletion aperture, while preserving exact adoption across tombstones and stale writers?

## Factorial and fixture

Use a full factorial of semantic node counts **256/1,000/5,000**, directed background out-degree **0/2/8**, and deleted-hub total incident degree **1/4/32/128** (36 cells). Keep one graph-resident mixed rule fixed across cells: change one node attribute, remove one edge, add one derived node and edge, and delete one hub with cascading incident-edge removal. The focus fact, peer, and hub are excluded from the density-controlled ring; all other live nodes, including hub spokes, participate. Each such node gets exactly the assigned number of outgoing ring edges. This holds background edge count at `out_degree × (live_nodes − 3)` in every aperture cell, so node count and assigned background density stay fixed while only the hub's explicit spokes vary. Record exact actual node/edge counts and the deletion incident-edge count.

Each cell has four deterministic seeds in each of three fresh workers (12 paired trials per cell; 432 total). Seed/cell combinations assign tombstone layout `none`, four interior random holes, four trailing holes, or a mixed layout with random and trailing holes. Add the requested number of live nodes plus deleted slots before constructing background edges. Counterbalance legacy full-graph versus targeted-native commit order by worker, seed, and cell. Use one successful rehearsal and default refusal per fixture, then commit identical isolated branches using either implementation. Uninstrumented commit latency is the primary cost measure.

For each authorized result, independently apply the declared effects to the complete pre-imagination graph, including cascading hub deletion and the returned added-node ID. Require exact graph equality, rehearsal and refusal isolation, expected rule/write kinds, and identical ID allocation across paths.

## Stale-writer challenge

For every factorial cell in each worker (108 additional cases), inject an unrelated concurrent writer after targeted commit planning but before native apply. Require revision rejection, preservation of the competing write, no proposal content writeback, and unchanged fact/link/hub state. These cases gate correctness and are not performance samples.

## Integrity and limits

Use repository engine-build provenance; lock this protocol, runner, Python/Rust implementation sources, build manifest, and loaded native binary. Require 36 cells, 432 clean pairs, 108 conflict cases, three unique PIDs, and all semantic/isolation/conflict checks before reporting cost. Report per-cell paired medians and wins. This directed-circulant model is synthetic; finite results do not establish asymptotic complexity, natural-graph prevalence, learned proposal quality, or task utility. Manifold assessment remains in commit cost and is not varied here.
