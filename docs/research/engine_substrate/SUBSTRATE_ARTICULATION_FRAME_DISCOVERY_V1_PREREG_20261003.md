# Articulation-based frame-discovery baseline v1 preregistration (2026-10-03)

## Question

Can topology alone recover useful task frames from captured substrate graphs?
This tests the simplest cheap-cut baseline against existing graph snapshots and
independent owner annotations. It does not claim that articulation points are
a substrate-native learner or that owner annotations are perfect semantic
truth.

## Locked inputs and proposal

Use all 78 graph snapshots from the three source families in structural census
v1.3: Bigville dynamic-link captures (63), connected-conversation captures
(12), and discourse connected-task captures (3). Reuse the source-census
projection exactly: simple undirected graph, self-loops excluded, duplicate
undirected edges collapsed. The only proposal rule is: find every articulation
vertex, remove all such vertices simultaneously, and use the resulting
connected components as proposed frames. Do not inspect frame-owner labels when
finding articulations or components. Treat removed vertices as candidate
boundary nodes; components with no annotated owner are not scored as frames.

Owner labels from the upstream captures are held out for scoring. For labeled
nodes surviving the cut, compute coverage, component purity, pairwise
same-frame precision/recall/F1, false-join pairs, and false-split pairs.
Also report what fraction of annotated cross-owner and same-owner edges touch a
removed articulation node. Report each family and every snapshot; do not pool
away failures or count repeated topologies as independent graph families.

## Gates

1. Lock all 78 upstream graph/owner snapshots, original source locks and
   result documents, structural-census v1.3 implementation, proposal code,
   protocol, and analyzer.
2. Reconstruct 78 unique source-run/checkpoint rows with deterministic graph
   identities; independently reconstruct each result in the analyzer.
3. Validate every returned articulation set by removing it and recomputing
   connected components; validate coverage and pairwise metrics from raw owner
   annotations.
4. Report all graph families and the complete per-snapshot distribution.
   Gate success means measurement integrity only; capability success is
   judged from coverage, purity, pairwise F1, false joins/splits, and whether
   the baseline works on held-out task families.

This is a retrospective evaluation on three selected graph families. The
owner annotations are task/runtime labels rather than independently adjudicated
semantic frames. The graph projection loses direction, relation type, and
factor scope. A high score would motivate factor-scope and semantic-parity
tests, not prove a safe operational decomposition. A low score would show
articulation topology alone is insufficient for these captures.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_articulation_frame_discovery_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_articulation_frame_discovery_v1.py`
- Lock: `evaluation/substrate_capability/substrate_articulation_frame_discovery_v1_lock_20261003.json`
- Capture: `evaluation/reports/substrate_articulation_frame_discovery_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_articulation_frame_discovery_v1_analysis_20261003.json`
