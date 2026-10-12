# Matched frame-topology scaling preregistration

**Lock date:** 2026-09-26, before capture.  
**Question:** At fixed frame/node/rule counts and edge count, how do native event scheduling and full closure compare across sparse chain, bounded-degree tree, and high-fanout star topologies? Do candidate and Term-evaluation counters explain observed cost?

## Workload

Topologies: directed chain, balanced binary tree, and directed star rooted at frame 0. Sizes are N ∈ {8,16,32,64} frames, each with one Microtheory and one Concept, and N−1 `causal_influence` edges. Every arm has the same graph-authored rule family: propagate state 1 forward over active edges, retract state 1 after the source resets to 0, and finalize/retract a frame-local `observed` flag from that frame's Concept state. Start from all-zero state, externally set root state to 1 and settle, then reset root to 0 and settle. The event worker is seeded at the root frame after each host intervention, then queues only native mutation-reported owners. Full closure uses `run_rules_report`.

Five fresh paired repetitions per topology/size. Add one event ablation per pair that drops the highest-index leaf owner's notification during activation; the leaf's state can be updated by an upstream rule, but its frame-local `observed` flag must stay stale. Enable the native scale audit on both arms and record candidate enumeration, Term evaluations/units, progress applications, scoped turns/enqueues, wall time, and full state projections after both transitions. Alternate arm order. Lock preregistration, runner, Rust sources, native artifact, and source fingerprint.

## Gates

1. Graph cardinalities are matched: N frames, N Concepts, N−1 dependency edges, and identical rule counts across topology variants.
2. Every full arm reaches reported fixed points after activation and retraction.
3. Every event arm settles to an empty queue without budget/deferred exit and exactly matches full state after both transitions.
4. Owner notifications cover all changed frames in the connected topology.
5. The omitted-leaf ablation leaves that leaf's `observed` flag stale and differs from the full activation projection.
6. Audit counters and source/build fingerprints are present and internally consistent.

## Claim boundary

This is a generated, monotone one-bit propagation workload with hand-authored frame ownership and three fixed topologies. It separates topology effects at matched size; it does not establish task-distribution prevalence, general tractability, learned partition quality, or production CPU performance. Audit instrumentation is enabled for both arms and timing includes instrumented work; interpret counters as primary and wall time as descriptive.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_frame_topology_matched_scale_v1.py
python3 scripts/analyze_substrate_frame_topology_matched_scale_v1.py
```
