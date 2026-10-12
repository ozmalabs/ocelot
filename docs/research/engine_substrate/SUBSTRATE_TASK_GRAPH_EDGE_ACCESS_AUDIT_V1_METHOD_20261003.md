# Task-graph edge/access audit v1 method

Date: 2026-10-03  
Status: retrospective exploratory analysis of already locked captures.

This audit asks whether the simple undirected graph projections in the task-graph structural census correspond to the available runtime dependency evidence. The captures were inspected before this audit was formalized, so its descriptive results are exploratory, not confirmatory.

For every captured snapshot, count typed directed edges and node types, then independently reconstruct the simple undirected projection. For Bigville, compare captured `term_edge_read` and `term_edge_attr_read` events with typed directed edges by source, peer, and edge type; report event multiplicity separately from distinct observed pairs. Report the producer's `reads_any` result, its partition refusal, and its task-dependency pair/width metrics. Treat runtime access tracing as partial, even when no events were dropped.

For the connected-conversation and discourse captures, independently rebuild the producer's frame interaction graph: direct edges between differently owned task nodes, plus a clique among frames touching the same unowned boundary node. Compare this owner-derived graph with the full-node undirected projection. Report static rule read/write scopes and concrete trace coverage where captured. Missing access traces stay missing; do not infer that no observed trace means no dependency.

All inputs are the source-locked captures profiled by structural census v1.3. Gates verify input locks/checks, source stability, complete snapshot coverage, trace-to-edge correspondence for observed Bigville edge reads, frame-interaction reconstruction, and exact agreement between the repeated structural census metrics and independent projection reconstruction. The result may show correspondence or a measurement gap; it cannot establish semantic partition safety, inference-factor scope, natural-task prevalence, or a speedup.
