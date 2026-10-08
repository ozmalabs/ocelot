# Concurrent reusable snapshot fork v1 preregistration

Date: 2026-10-01

## Question

Can the immutable Rust `ExperimentSnapshot` be shared safely across threads while each consumer forks and mutates an isolated branch? Does concurrent fanout reduce total branch setup time compared with serial use of the same snapshot at larger substrate sizes?

## Frozen protocol

- Compile-time assert `ExperimentSnapshot: Send + Sync`, then share one `Arc<ExperimentSnapshot>` across native Rust threads.
- Build isolated-node graph fixtures of 771, 10,771, and 50,771 nodes, capture one immutable snapshot, and compare serial versus simultaneous fork-plus-one-branch-node-write batches at fanouts 1, 4, and 16.
- Run five paired measured repeats in each of the nine size × fanout cells. Alternate arm order serial→concurrent and concurrent→serial by repeat parity. Snapshot construction and fixture generation are timed separately from batch fork-and-write.
- Each concurrent worker waits on a barrier before starting its per-worker timer; batch timing includes dispatch, thread scheduling, branch fork/write, and joining all workers. Serial batch time includes the same branch fork/write/drop work without thread creation.
- For every arm, check each branch has exactly one private node and no edges, the primary is unchanged, and a later snapshot fork returns exactly the base nodes with no branch-only type.
- Use the repository Cargo lockfile and the current Rust engine sources; verify engine build provenance before running and record runner, manifest, lockfile, binary, and source hashes.

## Gates and reporting

Require successful Send+Sync compilation, all nine cells, five paired repeats per cell, alternating arm order, primary/sibling/captured-base isolation, and current source/native provenance. Report all repeats, medians, per-worker timings, and serial/concurrent ratios. No speed threshold is imposed: the purpose is to determine whether the reusable immutable branch contract supports correct native concurrency and where thread setup pays off.

## Limits

This is native Rust concurrency on one host with synthetic isolated-node graphs. It measures branch creation and one mutation, not concurrent rule execution, shared live `Substrate` mutation, lock contention in Python bindings, cancellation, resident-memory reclamation, natural workloads, or serving integration. `Send + Sync` permits safe cross-thread sharing; it does not by itself establish deterministic semantic results for arbitrary concurrent execution.
