# Copy-on-write snapshot parallel rule closure v1 preregistration

Date: 2026-10-01

## Question

Can independent branches created from one immutable snapshot execute the same real native rule closure in parallel, preserve branch isolation, and improve total throughput at larger graph sizes/fanouts? What whole-process PSS delta appears while one versus many derived branches remain live?

## Frozen workload and controls

- Build a ring graph with 771, 10,771, or 50,771 nodes and one `thread_rule_input` edge per node.
- Install one native one-edge rule that matches each input edge and adds a corresponding `thread_rule_output` edge. One closure must produce exactly N output edges and reach fixed point.
- Pilot deviation, frozen before the confirmatory panel: the rule's `AddEdge` effect reads its output edge type for duplicate suppression, so the engine correctly does not certify disjoint read/write sets or `batch_safe`. Preserve that rule's real semantics with `batch=false`; measure concurrency across independent branches only. This is not a measure of within-rule Rayon batching. A provably batch-safe rule is a separate experiment.
- Rayon is not part of the measured path; independent branch concurrency uses native Rust threads.
- Compare reusable shared-graph-page snapshots with eager full-copy branches. For each storage path, run serial fanouts 1/4/16 and simultaneous native-thread fanouts 1/4/16. Complete five paired repeats for each graph size × fanout cell. Alternate the four timing-arm orders between two fixed schedules.
- Each branch performs `fork + run_rules + fixed-point verification`; the concurrent batch includes worker creation, dispatch, join, and branch drop. Record per-branch closure duration and whole-batch wall time.
- In a separate memory sample, retain one completed branch and then fanout completed branches, sample Linux PSS while branches are live, drop them, and sample again. Keep the primary plus both reusable base controls resident for all cells.
- Require all branches to produce exactly N derived edges; check primary counts/revision, no output edges in a later fork from either captured base, identical branch semantics, and terminal closure.

## Gates and reporting

Require all 9 size × fanout cells, five repeats in each of four arms, balanced arm order, a complete native rule closure, fixed-point termination, primary/snapshot isolation, current engine/source fingerprints, and a source-hashed binary. Report every repeat, closure and batch times, PSS deltas, and paired win counts. No speed or reclamation threshold is imposed.

## Limits

This is a synthetic one-rule workload and one host. The rule has a single edge clause and a single additive effect; it does not estimate natural-task coverage, thoughtexperiment candidate utility, arbitrary rule parallel safety, mutation of one shared live substrate, or serving integration. PSS is current whole-process accounting rather than exact heap ownership or kernel peak memory; post-drop PSS cannot prove reclamation. This rule's batch mode is disabled because its actual read/write sets overlap; results attribute parallelism to independent branches.
