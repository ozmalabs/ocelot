# TypedGraph COW shard-count comparison v7 preregistration

Date: 2026-10-06

## Question

Does increasing `CowShardedMap` shard count from the production baseline 64 to
128/256/512 improve real `TypedGraph` branch mutations, after accounting for
the whole set of graph index maps and exact queries?

## Arms and workloads

Build the same locked graph mutation worker four times, selecting default
shard count 64, 128, 256, or 512 through mutually exclusive Cargo features.
Use N=7,164, 16,384, and 50,771 nodes, each with a unique indexed integer
attribute. For each size and shard count, retain the existing 21 paired
mutations (set attribute, insert, delete, retype), eager-clone comparison,
exact query and typed-order assertions, parent/sibling isolation, and
delete/compaction/reuse/restore control. Record the median fork and write time.
Add a deterministic exact full-query sweep and process RSS snapshots before
and after fixture construction and after the capture.

## Gates and analysis

Every existing mutation, ordering, isolation, reuse, and attribute-index gate
must pass in all 12 size/shard cells. Report paired per-cell COW timings and
query sweeps; compare candidates against 64 within the same capture. Report
RSS as process-level and page-granular, not allocator-exact. No shard count is
promoted solely from this synthetic benchmark. A candidate must next pass
representative rule-closure and live workload measurements before production
selection.

This is a graph-engine microbenchmark, not evidence of natural task prevalence,
general frame locality, autonomous learning, or end-to-end capability.

## Timing replication amendment (2026-10-06)

The initial source-locked capture passed semantic gates but showed bimodal
small-graph insert timings within a worker, consistent with substantial
time-varying host noise. Treat that pass as a diagnostic only for timings. The
confirmatory capture runs three fresh worker processes per size/shard cell,
with deterministic rotation of shard-count order across replicates and graph
sizes. Each worker retains 21 repetitions and all original assertions. Compare
medians across the three fresh-process medians; preserve within-worker sample
distributions as a noise diagnostic. Correctness results from the first
capture remain valid, while shard-performance conclusions require the
amended replicated capture.
