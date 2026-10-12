# Thoughtexperiment journal mutation matrix v1 preregistration

Date: 2026-10-04

## Question

Does the current Rust `TypedGraph` before-image journal produce the same
semantic graph diff as a whole-graph oracle for each supported mutation
entrypoint and restore/checkpoint pattern relevant to thoughtexperiment
residuals?

## Method

Compile and run the standalone current-source evaluator
`runners/dsl/src/bin/thoughtexperiment_journal_mutation_matrix_v1.rs` from the
`runners/dsl` Cargo package. Each row constructs the same three-node,
two-edge graph; starts `begin_experiment_delta_log`; applies one fixed
operation sequence; and compares `graph_experiment_delta` from the journal
with `graph_diff(graph_to_value(before), graph_to_value(after))`. The live
restore row replaces a node's type and full attributes under its existing ID.
The phase row makes a pre-checkpoint write, checkpoints, then makes another
node write and inserts an edge; total and derived-only journal outputs are
checked against their matching graph snapshots. The untracked control makes
one journaled write, finishes capture, then writes a different node and
requires the whole-graph oracle to diverge from the journal receipt.

The fixed matrix is: node attribute set/removal/type change; live, fresh, and
tombstoned identity restoration (delete then restore the same ID); node
deletion with incident edges; node insertion; edge
insertion/replacement/attribute mutation/single deletion/batch deletion;
repeated writes; phase checkpoint; and post-capture divergence. The matrix
uses one fixed sequence per row; it is not exhaustive over values, IDs, or
operation orderings.

## Gates

1. Lock this protocol, runner, graph/persistence/value/interner sources, and
   Cargo manifest/lockfile before compilation or execution.
2. Require every captured journal diff to equal its whole-graph diff,
   including node type, attributes, edge structure, and edge attributes.
3. Require the phase journal to equal the post-checkpoint full graph diff.
4. Require the post-capture mutation control to demonstrate that the journal
   does not claim to detect arbitrary later/untracked state divergence.
5. Preserve raw JSON output and source/build fingerprints. Any source or
   protocol edit after lock invalidates the run and requires a new version.

## Claim limits

Passing this finite mutation matrix establishes parity only for the enumerated
public `TypedGraph` operations and fixed cases. It does not establish all
possible runtime paths, concurrency safety, rule-engine write coverage, or
global branch/primary equality. Exact whole-graph parity remains required
where arbitrary divergence must be excluded. No performance claim is made.
