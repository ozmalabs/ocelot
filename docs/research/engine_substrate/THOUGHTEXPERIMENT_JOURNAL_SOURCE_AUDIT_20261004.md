# Thoughtexperiment journal source audit — 2026-10-04

## Scope and method

This is a source audit of `TypedGraph`'s semantic mutation entry points and
the optional before-image hooks used by `begin_experiment_delta_log`. It is
not a dynamic coverage measurement, a compiled verification, or a rerun of
the locked touched-object parity experiment. That experiment's results apply
to its recorded source lock only.

`TypedGraph` stores its node, edge, attribute, and adjacency slabs in private
fields. The public semantic writes in `runners/dsl/src/graph.rs` route through
`node_mut`, `insert_node`, `insert_edge`, `delete_edge`,
`delete_edges_batch`, `edge_attrs_mut`, `delete_node`, node-attribute/type
setters, or identity-preserving `restore_node`/`restore_edge`. Node setters
use `node_mut`; edge insertion/deletion and mutable edge-attribute access
record edge before-images. Node deletion records the node and cascaded edge
deletions.

## Finding and correction

The audit found that `restore_node` always called `log_node_added` after
replacing the slot. When the ID was already live, the journal recorded an
absent before-image instead of the previous node record. A residual could
therefore misdescribe that replacement as an insertion. The current source
now calls `log_node_mutation` before replacing a live node and uses
`log_node_added` only for a fresh or tombstoned identity. This retains the
pre-replacement type, attributes, and phase checkpoint state through the
existing journal helper.

## Evidence boundary and next gate

This is a static source finding and narrowly scoped source correction. No
project tests, build, or thoughtexperiment worker was run for this correction.
The v1.1 touched-object parity capture remains valid for its locked revision;
it does not establish coverage for the corrected current source. Before
claiming journal completeness, add a preregistered current-source mutation
matrix covering live-node restoration/retyping, fresh and tombstoned
restoration, node setters/deletion, edge replacement/attribute changes,
single and batch deletion, phase checkpoints, and repeated writes. Compare
each journal patch with a whole-graph oracle and include deliberately
untracked divergence controls. Keep the global audit requirement until that
matrix passes and mutation entry points remain encapsulated.
