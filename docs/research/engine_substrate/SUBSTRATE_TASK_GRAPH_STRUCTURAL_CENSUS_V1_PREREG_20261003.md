# Task-graph structural census v1 preregistration

Date: 2026-10-03  
Status: preregistered retrospective analysis of prior source-locked task captures.

## Question

Do task-derived substrate graph snapshots from distinct workload families exhibit disconnected components, single-vertex cuts, or low min-fill width bounds, and how do those structural profiles change over captured execution checkpoints?

## Frozen inputs

Use the accepted source-locked captures, without rerunning or modifying them:

1. Bigville dynamic-link cut capture: nine worker traces × seven graph checkpoints (63 snapshots).
2. Connected-conversation boundary panel: three workers × four task cases (12 snapshots).
3. Discourse connected-task census v2.1: three fresh-process final graphs (three snapshots).

Require every upstream capture check to pass and each capture's own lock/source checks to remain present. Total planned observations: 78. These are generated/authored task graphs from three distinct workloads, not a random sample of natural use.

## Measurements

Project each graph to a simple undirected graph over its captured nodes, ignoring edge direction, type, and attributes. Preserve raw node/edge counts and count loops and duplicate undirected pairs separately. Report component sizes, degree summaries, articulation count and balanced-cut profile, owner-labeled edge crossings when upstream frame-owner metadata exists, and deterministic min-fill elimination upper bound. Independently validate the min-fill elimination order as a treewidth upper-bound certificate.

Separator interpretation is limited to what is computed exactly: disconnected inputs have a size-zero separator; connected inputs with articulation vertices have minimum separator size one; connected inputs without articulation vertices are reported as “minimum size at least two, not computed.” Do not search higher-order cuts in this census. Analyze every snapshot; cache only structural metrics for identical canonical graph hashes.

Report graph-profile distributions by family and checkpoint, extraction/search CPU and wall time, shared manifest hardware/toolchain/dirty-workspace provenance, parent stdout/stderr capture, and peak RSS. Use existing owner labels only for an explicit comparison profile; they are not supplied to the graph-only structural measurements.

## Gates

1. All three upstream source-locked captures have all registered gates true and unchanged hashes.
2. Coverage equals 63 Bigville, 12 connected-conversation, and 3 discourse snapshots.
3. Every graph hash, component profile, articulation count, and owner-crossing count is independently recomputed from the locked source graph.
4. Every returned min-fill order contains each node once and its independently simulated elimination width equals the reported upper bound.
5. Shared `substrate-run-manifest-v1` includes runner, analyzer, preregistration, upstream captures/locks, graph-width implementation, and manifest helper; stdout/stderr capture and CPU/RSS fields are present.

## Claim boundary and next gate

This is a structural census over three existing generated/authored task families. It can test whether zero/one-vertex separators and small min-fill bounds occur in these snapshots and how often owner cuts align with graph structure. It does not show that edges are inference factors, that omitted boundaries preserve rule closure, that a solver benefits, or that the sample represents natural tasks. Any inference claim requires a separate factor-scope audit and exact semantic parity test. Any engine-locality claim requires C2a access fidelity and native partition execution.
