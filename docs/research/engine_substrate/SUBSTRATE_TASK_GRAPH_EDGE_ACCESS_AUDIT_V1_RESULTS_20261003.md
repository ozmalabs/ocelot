# Task-graph edge/access audit v1 results

Date: 2026-10-03  
Status: exploratory retrospective audit; runner and independent-analysis gates pass.

## Findings

| Workload | Full-node projection | Captured access / frame interaction evidence | What it establishes |
|---|---|---|---|
| Bigville dynamic link | 63 snapshots; the producer's dependency graph has min-fill upper bound 2 in every snapshot | The producer excludes `has_concept` ownership links from dependency-pair construction. Across snapshots, 317,056 aggregated `term_edge_read` / `term_edge_attr_read` events refer to `causal_influence`; all observed typed directed accesses match edges present in the captured graph. All nine workers report `reads_any=True`; partition execution is refused in all 63 snapshots. | Captured edge reads have concrete correspondence, but the rule-level wildcard prevents safe frame-scoped closure in this experiment. The full graph's width 3 is not the operative dependency width. |
| Connected-conversation panel | All 12 snapshots are disconnected in the simple undirected projection | Reconstructing direct cross-owner edges plus shared-boundary incidence yields a complete frame-interaction graph in all 12 cases. Its exact width is 1 in the three two-goal cases, 3 in six four-frame cases, and 7 in the three eight-goal cases. Static rule access sets and concrete runtime access traces are absent from this capture. | A disconnected full-node projection does not imply independent task frames; shared unowned boundary nodes couple every frame in these cases. |
| Discourse connected task | All three snapshots are disconnected in the simple undirected projection | The owner-derived interaction graph is K3 in all three runs, with two direct cross-frame edges and seven shared boundary nodes. Twelve static rule records across three runs have no wildcard reads/writes. The traced arm records only eight `term_attr_read` events; no edge reads are observed in the captured trace. | The graph-based frame coupling and static rule scopes exist, but concrete trace coverage is too sparse to establish dynamic dependency completeness. |

The independent analyzer matches all 78 projection component profiles against structural census v1.3 and reconstructs each producer's frame-interaction graph from captured graph edges and owner labels. It verifies zero missing typed edge matches for the observed Bigville reads, all capture lock/source checks, the shared run manifest, CPU/RSS fields, and the parent console-log hash. Audit wall/CPU time was 6.01 s, with 285 MB peak RSS.

## Tractability implication

The task-graph census found low-width undirected projections, but this audit shows that those projections do not faithfully represent computation on their own. The connected-conversation and discourse full-node graphs are disconnected while their frame-level interaction graphs are complete. Bigville's task-dependency model is narrower than its full graph, but the native partition path still correctly refuses because static analysis reports wildcard reads. The tractability condition therefore needs a validated dependency model and boundary interface, plus semantic parity under actual execution. Structural sparsity is a useful screening signal, not a sufficient condition for factorization.

## Next gate

For a new workload, record explicit read/write scopes and concrete accesses with rule attribution, including host/native work outside a rule. Derive the partition interface from those scopes and accesses, then run monolithic and partitioned closure/inference from identical snapshots. Require exact final-state and output parity under dynamic updates, deletes/reuse, shared boundary nodes, and high-coupling controls. Measure partition discovery, graph extraction, message construction, scheduling, memory, trace overhead, and solver time. The conversation family currently lacks the access evidence needed to begin this gate without a fresh instrumented capture.

This was a retrospective exploratory audit because the source captures and projection result were inspected before its method was formalized. It is descriptive evidence, not a preregistered confirmatory result or a general estimate of natural-task prevalence.

## Provenance

- [Method](SUBSTRATE_TASK_GRAPH_EDGE_ACCESS_AUDIT_V1_METHOD_20261003.md)
- [Structural census result](SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_RESULTS_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_task_graph_edge_access_audit_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_task_graph_edge_access_audit_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_task_graph_edge_access_audit_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/substrate_task_graph_edge_access_audit_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/substrate_task_graph_edge_access_audit_v1_analysis_20261003.json)
