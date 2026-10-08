# Thoughtexperiment candidate branch scaling v2 (preregistration)

## Question

With task outcome and rule family held fixed, how do CoW branch setup and
native closure respond independently to total background size, task-frame
aperture, separator width, and sparse topology? This extends v1's fully
disconnected background with an executable frame boundary that the rule must
inspect.

## Factorial design

The panel crosses two background topologies (directed path and binary tree),
three background sizes (128, 1,024, 8,192 nodes), three task apertures (2, 8,
32 context nodes in a matched chain), and three separator widths (1, 8, 32
edges from the first task context node into the background): 54 cells. Each
cell has three fresh processes and three paired no-op/candidate repetitions.
The candidate changes only the live threshold `signal >= 0` to `signal >= 1`.
Every task input has signal zero. Both rules also require an `Exists` witness
on `boundary_link`; its neighbors are inserted as non-witness decoys followed
by one positive witness, so the boundary predicate examines the configured
separator before succeeding. Decoy topology edges use a different relation.

Measure shared-page fork, candidate rule installation, task-frame construction,
separator-edge insertion, native closure, and targeted output read separately.
Alternate no-op/candidate order within each worker. Add one separate
scale-audit candidate probe per worker/cell and require its per-rule
per-rule `Exists` and term-unit counters to reconcile with global counters and
show that examined neighbors equal the registered separator width; exclude
this instrumented probe from wall-time summaries. Record exact result,
primary graph digest and rule revision/hash, native graph size, process RSS
snapshots, and source hashes. RSS remains diagnostic; no memory delta claim is
registered.

## Acceptance and reporting

All 972 episodes must return the expected no-op/candidate outputs, match across
replicates, preserve primary graph/rule state, and reproduce locked sources.
Report medians for each cell and factor slices; do not collapse across
topology, aperture, or boundary width. The panel is one authored rule family
on one host. It does not establish natural-task prevalence, asymptotic
complexity, arbitrary graph width, inference cost, or multi-host behavior.
