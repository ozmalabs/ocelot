# GenInfer scope-index lifecycle v1 preregistration

## Question

On the live native Substrate GenInfer route, does an optional `(ShapeSignature, scope_id)` index repay its build, maintenance, branch-fork, and restore costs as the codebook population grows, while preserving exact inferred outputs?

This is a synthetic scaling probe for one existing route. Frame scopes and decoys are harness-authored; no claim about automatic frame discovery or natural-task prevalence follows.

## Protocol

Use the current `boot_core()` plus `shape_decode_loop` and `GenInfer` rule path. Compare the same `frame_scoped` fixture in scan and indexed arms, with 0, 1,000, and 10,000 unrelated `ShapeSignature` decoys and three fresh worker processes per cell. Each positive fixture has two distinct frames and the same locked integer-linear transformations as the preceding scope-index trace. Decoys carry nonmatching scope IDs and empty signatures; they increase the searched typed population without changing target membership. The index arm backfills after decoy creation, then both arms insert the same task parts and observations.

Before closure, measure index build/backfill, task-fixture insertion, full `Substrate.fork_shared_graph_pages_experiment()` time, a fixed 32-decoy scope-attribute mutation batch on a forked branch, graph serialization, graph restore, and optional post-restore index rebuild. Measure production `run_rules()` wall and process CPU time without access tracing. Capture exact task statuses, transformation receipts, generator inventory, rule work result, graph sizes, and peak RSS. The scan and index arms must agree on frame membership, exact outputs/receipts, target-generator acquisition, and candidate work; the branch mutation must preserve the parent and keep indexed buckets equal to a full-scan oracle; restored graph serialization and re-declared index membership must match exactly.

Use three population levels and three fresh workers per arm/cell (18 workers). Source-lock the Python harness, independent analyzer, protocol, native build manifest/binary, relevant Rust/Python sources, and seed dependency closure. Refuse stale native builds and source drift. Preserve failed captures and amend protocol before any retry.

## Analysis

- Report each component time separately and the indexed-minus-scan closure difference; do not claim a speedup if exact outputs/work fail parity.
- Report the fork and mutation tax as measured for these branches; do not treat graph serialization as full Substrate serialization.
- Report medians and all worker values. Three replicates are a pilot, not a calibrated tail-latency estimate.
- Compare growth with typed population and decoy count. Do not infer complexity class or natural-task distribution from three synthetic sizes.
- Separate exact output parity, internal work parity, operational latency, memory, and scope provenance.

## Advancement gate

This experiment advances only the live-route index-lifecycle gate. A positive decision for production admission additionally requires task-representative query/mutation rates, a reliable source-side scope producer, current end-to-end fork/restore semantics, and replicated memory/timing results. Index presence must remain opt-in until those conditions are measured.
