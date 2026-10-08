# Task-graph structural census v1.3 results

Date: 2026-10-03  
Status: runner gates pass; independent analysis passes.

## Result

The preregistered retrospective census profiles 78 graph snapshots from three previously source-locked task-graph captures. The v1.3 runner used the shared `substrate-run-manifest-v1`, captured console output, and recorded CPU time and peak RSS. The source lock covers the runner, independent analyzer, protocol, graph-width implementation, upstream captures, locks, and result documents. The analyzer independently reconstructed each simple undirected projection and validated each returned min-fill elimination order as a width upper-bound certificate.

| Source family | Snapshots | Distinct topologies | Nodes (min / median / max) | Edges (min / median / max) | Separator result counts | Min-fill width upper bound (min / median / max) |
|---|---:|---:|---:|---:|---|---:|
| Bigville dynamic link | 63 | 11 | 700 / 700 / 700 | 1,100 / 1,166 / 1,200 | disconnected 36; articulation 27 | 3 / 3 / 3 |
| Connected-conversation panel | 12 | 4 | 259 / 265.5 / 289 | 222 / 249.5 / 360 | disconnected 12 | 6 / 6.5 / 7 |
| Discourse connected task | 3 | 1 | 263 / 263 / 263 | 236 / 236 / 236 | disconnected 3 | 6 / 6 / 6 |

In the Bigville snapshots, articulation counts range from 199 to 200; known owner-crossing edges range from 0 to 100 (median 66). The conversation-panel snapshots have 50–51 articulation nodes and 3–15 known owner-crossing edges (median 6). The discourse snapshots each have 50 articulation nodes and two known owner-crossing edges. The disconnected status for the conversation and discourse families is calculated on the deliberately lossy undirected projection and should be read literally as a property of these projected captures.

The full run processed 16 distinct graph topologies in 10.17 s wall time and 10.17 s process CPU, with 278,028,288 bytes peak RSS on the recorded host. These are extraction and structural-profile costs, not native inference costs. Min-fill work over unique topologies totaled 3.11 s across the three families (2.86 s Bigville, 0.212 s conversation, 0.037 s discourse); repeated topologies reuse only structural metrics.

## Interpretation and limits

These captured graph projections are sparse and have small min-fill upper bounds, which is consistent with hierarchical sparsity in these selected workloads. The evidence does not establish that captured edges are factor scopes, that a cut preserves inference or rule closure, that owner labels identify semantically correct frames, or that these three authored/generated families represent natural task prevalence. Because direction, type, and edge attributes are discarded, the projection can create or erase structural properties relevant to computation. The min-fill values are upper bounds, not exact treewidths. Separator search stops at size one.

This closes the preregistered task-graph *structural profile* gate only. The next tractability gate is a factor-scope audit on source tasks, followed by an exact semantic-parity comparison between a graph-derived decomposition and a monolithic solver. Include connected and high-coupling controls, retain task labels only for stratification, and charge decomposition discovery, binding, updates, messages, and memory. Native partition scheduling and natural-use sampling remain later gates.

## Provenance and revisions

- [Preregistration](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_PREREG_20261003.md)
- [v1.1 adapter amendment](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_1_AMENDMENT_20261003.md)
- [v1.2 analyzer amendment](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_2_AMENDMENT_20261003.md)
- [v1.3 identity amendment](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_task_graph_structural_census_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3_lock_20261003.json)
- [Capture](../../../evaluation/reports/substrate_task_graph_structural_census_v1_3_20261003.json)
- [Independent analysis](../../../evaluation/reports/substrate_task_graph_structural_census_v1_3_analysis_20261003.json)

V1 and v1.1/v1.2 iteration artifacts are retained. V1.1 failed on an upstream `arm`/`replicate` schema mismatch before profiling; v1.2 completed the capture but its analyzer exposed endpoint-filtering and repeated-case identity defects. Only v1.3 is confirmatory. See each amendment for the precise correction and unchanged claim scope.
