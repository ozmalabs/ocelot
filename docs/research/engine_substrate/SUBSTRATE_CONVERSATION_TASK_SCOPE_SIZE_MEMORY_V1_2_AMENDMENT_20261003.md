# Size/memory v1.2 amendment: separate closure arms by process

Date: 2026-10-03  
Status: preregistered before v1.2 implementation and capture.  
Prior evidence: [v1.1 isolated size sweep](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_1_RESULTS_20261003.md)

## Question

How does whole-worker peak RSS differ among monolithic, verified full-fallback, and declared-anchor closure when each arm runs alone in a fresh process on the same locked graph-size/order/replicate cell?

## Design

Repeat the same 5 × 3 × 3 panel: shared-event decoy counts 0, 256, 1,024, 4,096, and 16,384; ascending, descending, and outside-in scope orders; three replicates. Launch one new process for each combination and arm, for 135 workers. Each worker materializes the same authored two-goal case and decoys, executes exactly one arm, records checkpoint/final graph digests, lifecycle statuses, graph dimensions, Candidate/Term counters, closure timing, and samples `ru_maxrss` before output serialization. Disable access tracing. The parent streams each compact result directly into a partial capture and keeps only PIDs and integrity flags, preventing parent-retained results from entering child RSS.

The fallback arm removes declared-anchor metadata from both the seed-loader and `boot_core` module lookup. The anchor arm uses the locked scope metadata. Monolithic closure retains the current all-graph route. The source lock includes runner/analyzer/protocol, native extension/build identity, Rust engine sources, rule seed, materializer, and task fixtures.

## Gates and interpretation

- Require 135 unique worker processes, exact schedule assignment, stable locked inputs, and all cells/arms present exactly once.
- Independently match each cell's final and checkpoint graph digests and goal lifecycle status across all three arms. Require fixed-point closure, anchor-path exercise, and zero anchor attempts/rejections plus positive full-fallback calls in fallback workers.
- Report per-arm median/min/max peak RSS, graph dimensions, Candidate/Term totals, and wall time at every size. RSS is whole-process maximum for that arm, including interpreter, graph materialization, graph representation/indexes, closure temporaries, and compact result summaries; it is not an allocation trace or native-only measurement.
- Treat all results as controlled synthetic workload evidence. Do not infer natural graph distributions or general tractability. A timeout or failed gate is retained and reported without dropping cells.
