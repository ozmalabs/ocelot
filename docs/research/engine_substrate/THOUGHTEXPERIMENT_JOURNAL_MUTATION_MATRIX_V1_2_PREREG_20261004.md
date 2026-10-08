# Thoughtexperiment journal mutation matrix v1.2 preregistration

Date: 2026-10-04

## Question

Does the current Rust `TypedGraph` before-image journal match the whole-graph
oracle across its public semantic mutation APIs, including direct mutable
node access, restoration, repeated writes, and checkpointed residuals?

## Method

Run `runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1_2.rs`
from the `runners/dsl` Cargo package in the `dev` profile. Each fixed case
starts from a three-node, two-edge graph, starts the journal, applies its
operation sequence, and compares `graph_experiment_delta` with
`graph_diff(graph_to_value(before), graph_to_value(after))`. The cases cover
direct `node_mut` attribute writes; node attribute set/removal and type
change; live, fresh, and tombstoned `restore_node`; node deletion with
incident edges; insertion; edge insertion/replacement/attribute mutation,
single and batch deletion; repeated writes; a phase checkpoint; and one
deliberate post-capture divergence control. The checkpoint case compares
`derived_only` with a full diff whose baseline is captured after the
checkpoint.

The executable is semantic only; no timings will be reported. Lock this
protocol, executable, capture wrapper, graph/persistence/value/interner
sources, Cargo manifest, and lockfile before compiling or running. Require
17 distinct rows, exact journal/full-diff equality in each row, phase equality
for the checkpoint case, and a global-diff divergence result for the
post-capture control. Preserve raw output, toolchain, binary hash, and locked
source hashes.

## Claim limits

Passing the enumerated cases demonstrates current-source parity for these
fixed calls and operation orders. It does not prove concurrency safety,
every possible use of public mutable references, complete application-level
mutation coverage, or whole-branch equality after arbitrary untracked writes.
Exact global parity remains required where arbitrary divergence must be
excluded. No performance or general tractability claim follows.
