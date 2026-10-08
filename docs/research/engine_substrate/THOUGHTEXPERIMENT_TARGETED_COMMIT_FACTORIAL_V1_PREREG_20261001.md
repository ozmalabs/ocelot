# Thoughtexperiment targeted commit factorial v1 — preregistration

**Date:** 2026-10-01  
**Question:** How does targeted residual commit cost vary independently with semantic node count, background edge density, and deletion aperture, and does exact allocation/adoption behavior hold across interior, trailing, and mixed tombstone layouts?

## Factorial and fixture

Use a full factorial of semantic node counts **256/1,000/5,000**, directed background out-degree **0/2/8**, and deleted-hub total incident degree **1/4/32/128** (36 cells). Keep a single graph-resident mixed rule fixed across cells: change one node attribute, remove one edge, add one derived node and edge, and delete one hub with cascading incident-edge removal. Context nodes form a seeded directed circulant graph at the assigned out-degree; context edges do not touch the focus fact, hub, or hub spokes. This holds rule work and focus structure fixed while independently crossing graph size, background density, and deletion aperture. Record actual live node/edge counts and incident-edge count.

Each cell has four deterministic seeds in each of three fresh workers (12 paired trials per cell, 432 total). Seed/cell combinations assign tombstone layout `none`, four interior random holes, four trailing holes, or a mixed layout with random and trailing holes. Create exactly the requested live node count plus deleted slots before adding background edges. Counterbalance legacy full-graph versus targeted native commit order by worker/seed/cell. Use one successful rehearsal and default refusal per fixture, then commit identical isolated branches with either backend. Record uninstrumented commit latency as the primary cost; separately count `graph_to_dict()` calls and targeted-query/ID access counts.

For each authorized result, build an independent complete-graph oracle from the pre-imagination graph, declared rule effects, cascade deletion, and the returned created-node ID. Require exact graph equality, unchanged rehearsal/refusal semantics, expected rule/write kinds, and identical ID allocation across both paths.

## Stale-writer challenge

For every factorial cell in each worker (108 additional cases), run a targeted commit whose native `apply_experiment_graph_delta` boundary injects an unrelated competing writer after planning but before the real apply. Require revision rejection, preservation of the competing write, no proposal content writeback, and unchanged fact/link/hub state. These conflict cases are correctness gates, not performance samples.

## Integrity and decision rule

Use the repository engine-build provenance gate; lock the protocol, runner, relevant Python/Rust sources, build manifest, and loaded native binary. Require 36 cells, 432 clean paired trials, 108 stale-writer cases, three distinct PIDs, and all exactness/isolation/conflict checks before reporting timing. Report per-cell paired medians, pair wins, and phase-free total costs. Do not claim a complexity class from these finite cells. If performance interactions appear, follow up with more levels/hosts; preserve any correctness failures as failures.

## Limits

The directed-circulant background and fixed rule are synthetic. Degree is controlled but does not represent natural graph structure. The study estimates mechanism cost, not learned proposal quality, task utility, or task prevalence. Manifold assessment remains part of commit cost and is not separately manipulated here.
