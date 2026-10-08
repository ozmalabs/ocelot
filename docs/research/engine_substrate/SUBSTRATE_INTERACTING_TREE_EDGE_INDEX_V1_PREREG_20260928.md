# High-degree edge lookup and topology replay v1 preregistration

**Question:** does an adaptive target index for high-degree `(source, edge type)` buckets preserve graph semantics while removing the high-fanout edge-construction bottleneck identified in the source-locked interacting-tree panel?

## Conditions

Use the existing interacting-tree worker unchanged for the measured workload: N=100,000 and 1,000,000; balanced binary tree and star; three fresh uninstrumented processes per cell. The worker separately times node creation, edge creation, rule installation, closure, and terminal validation. Use the same host, Python/native interface, node attributes, two propagation rules, edge multiplicity, and terminal oracle as the prior v1 panel. Compare new measurements with the three uninstrumented replicates in the locked v1 capture. The prior source and raw files remain immutable; this is a new implementation replay, not a replacement of v1.

## Semantic controls

Exercise target-index creation at the threshold, duplicate insertion while indexed, edge-attribute replacement on duplicate, deletion while indexed, demotion below threshold, lookup after demotion, and reinsertion to recreate the index. Also exercise a low-degree bucket. Require exact edge counts, `has_edge` results, and final attributes after every stage. The scale workers independently require exact graph counts, fixed point, all nodes active, no pending/ready nodes, zero budget overshoot, and correct sampled parents/attributes.

## Provenance and reporting

Lock the runner, analyzer, this protocol, the reused v1 worker, `graph.rs`, native build manifest and native extension. Require a fresh native build and stable pre/post source hashes in every worker. Retain raw per-worker phase timings and source snapshots. Report paired condition medians and per-replicate speed ratios; timing is descriptive with three replicates. Do not claim a general asymptotic bound from these two topologies.

## Gate and limits

The implementation gate passes only if every semantic control and worker oracle passes, the source lock is stable, all 12 new workers have unique PIDs, and the independent analyzer reconciles every cell against the prior capture. If correctness fails, stop and do not interpret timing. This evaluates one graph builder and duplicate-check path; it does not measure high-degree edge deletion throughput, inference, learned frames, or general workload prevalence.
