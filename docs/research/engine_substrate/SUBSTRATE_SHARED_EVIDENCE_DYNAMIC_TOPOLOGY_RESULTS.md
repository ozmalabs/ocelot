# Randomized dynamic boundary results (v1.2)

## Semantic gates

The v1.2 locked study completed all 81 workers on random connected spanning trees at N=12/24/48, using three fixed graph seeds and three process replicates. It passed all 27 full/scoped comparisons through six checkpoints: initial; tree-boundary insertion/activation; insertion of new non-tree cross-frame boundaries plus signal update; explicit retraction and deletion of half the new boundaries; re-insertion of those endpoint pairs plus a new value; and final retraction/deletion. All 27 omitted-boundary controls left exactly the two outputs for the selected backbone boundary stale at checkpoints where its expected value was nonzero; no other outputs were stale. The independent audit verifies source hashes, graph-family counts, all state projections, mutation timer arithmetic, and omission signatures.

## Measured work and time

Each size has nine paired observations (three graph seeds × three fresh-process replicates). Values below are medians across those pairs. Closure and graph/scope mutation timers are separate.

| Frames | Full candidates | Scoped candidates | Full Term evaluations | Scoped Term evaluations | Full closure | Scoped closure | Full mutation | Scoped mutation |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 458 | 10,164 | 3,994 | 86,116 | 0.281 ms | 2.601 ms | 0.292 ms | 0.295 ms |
| 24 | 950 | 42,956 | 8,282 | 364,032 | 0.448 ms | 10.565 ms | 0.584 ms | 0.611 ms |
| 48 | 1,934 | 176,036 | 16,862 | 1,492,452 | 0.713 ms | 41.613 ms | 1.135 ms | 1.189 ms |

At N=48, scoped closure records about 91× the candidate pairs and 89× the Term evaluations of full closure; median closure time is about 58× higher. Mutation time is similar between arms and remains much smaller than scoped closure at N=48. This isolates repeated broad scope matching as the dominant measured cost in this benchmark; it does not imply all scoped implementations or task families have this profile.

## What the mutations establish

New edges connect pairs absent from the initial random spanning tree. The harness installs endpoint evidence/state nodes and their `Microtheory.has_concept` memberships, inserts the `supports` edges, runs closure, then deactivates and settles before removing support and scope-membership edges. It records pre-closure input/partition edits and post-closure graph edits separately from closure. The parity result therefore covers caller-managed partition membership during dynamic boundary creation and removal. It does not show the engine discovering affected frames or updating memberships automatically.

The v1 run's false sensitivity predicate and v1.1 mutation timer contamination are both preserved with separate raw reports. V1.2 corrects the omission expectation at checkpoint 3 and the mutation timer boundaries without changing graph generation, semantic gates, or worker matrix.

## Limits and next gate

The graph family is generated sparse structure with N≤48 and three deterministic seeds. The two native copy/retract rules are authored for this probe; support-edge deletion follows explicit inactive-state settlement; scope visitation and membership maintenance are caller-driven. This is not natural task topology evidence, general truth maintenance, automatic notification completeness, or a complexity theorem. Next measure runtime-derived partitions and native effect-to-frame notifications on an authored task path, while retaining full closure and omitted-notification controls.

Artifacts: [v1.2 amendment](SUBSTRATE_SHARED_EVIDENCE_DYNAMIC_TOPOLOGY_V1_2_AMENDMENT_20260925.md), [runner](../../../scripts/substrate_shared_evidence_dynamic_topology_v1_2.py), [independent audit](../../../scripts/analyze_substrate_shared_evidence_dynamic_topology_v1_2.py), [raw report](../../../evaluation/reports/substrate_shared_evidence_dynamic_topology_v1_2_20260925.json), and [lock](../../../evaluation/substrate_capability/shared_evidence_dynamic_topology_v1_2_lock_20260925.json). Earlier locked versions are preserved: [v1 protocol](SUBSTRATE_SHARED_EVIDENCE_DYNAMIC_TOPOLOGY_PREREG_20260925.md), [v1 raw](../../../evaluation/reports/substrate_shared_evidence_dynamic_topology_20260925.json), [v1.1 amendment](SUBSTRATE_SHARED_EVIDENCE_DYNAMIC_TOPOLOGY_V1_1_AMENDMENT_20260925.md), and [v1.1 raw](../../../evaluation/reports/substrate_shared_evidence_dynamic_topology_v1_1_20260925.json).
