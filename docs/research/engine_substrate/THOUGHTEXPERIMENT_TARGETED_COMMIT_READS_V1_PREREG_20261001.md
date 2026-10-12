# Thoughtexperiment targeted commit reads v1 — preregistration

**Date:** 2026-10-01  
**Question:** Can `commit_imagination` preserve its revision-checked atomic semantics while replacing a full `graph_to_dict()` materialization with targeted native node/edge reads and a native next-live-node-ID query?

## Change under evaluation

The baseline commit path captures the graph/rule revision, serializes the complete live graph, constructs Python dictionaries of every node and edge, and consults only affected nodes/edges plus the maximum live node ID. The candidate keeps the same revision-first transaction and `apply_experiment_graph_delta`, but obtains the next ID from a native graph scan over node slots and checks only touched nodes/edges through native query methods. Preserve the current allocation rule (`max live NodeID + 1`), including tombstones and graphs whose largest allocated slot was deleted. All before-image checks and staged-apply conflict checks remain active.

## Gate

Run the existing four-family × 64/1,000-node × three-seed panel in three fresh workers. Require exact full-graph oracle parity, default refusal, primary isolation, expected conclusion/write kinds, explicit approved commit, and a tombstone-ID fixture proving allocation does not collide and matches baseline behavior. Capture uninstrumented `imagine`, reground, refusal, and approved-commit medians against the source-locked v1.1 baseline. Capture output of targeted query calls, ID allocation, and native staged apply separately in an instrumented diagnostic arm. A failed semantic gate invalidates all speed comparisons.

## Source/build integrity and limits

Hash the runner, protocol, Python/Rust sources, build manifest, and native binary; refuse stale engine builds. Preserve an eager/full-graph reference path as a differential control during the experiment. This synthetic panel does not establish natural-task prevalence, broad graph scaling, or performance on dense graphs. The result will justify only this commit implementation path and fixture family.
