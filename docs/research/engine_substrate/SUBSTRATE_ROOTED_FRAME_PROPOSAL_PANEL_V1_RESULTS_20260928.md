# Rooted frame-proposal panel v1 results (2026-09-28)

## Result

The amended three-worker capture passes all nine runner checks and five semantic/control checks. It preserves the first prompt's resolved self-report lifecycle and the known second-prompt route shortfall separately. All source/native inputs remain stable through the run; the task cuts, rooted-proposal structures, and semantic graph digest reproduce across workers. The independent analyzer passes all eight gates, including reconstruction of all 18 candidate frame sets and their cuts from the stored topology/type/attribute-key snapshots.

The final runtime graph has 25,021 nodes and 11,548 edges. Radius is undirected typed-edge distance from each inbound Message. The table reports one repeated signature per prompt across workers; boundary counts are exact for the proposed member set.

| Prompt | Radius | Proposed nodes | Crossing edge incidences | Distinct external nodes | Operational-label precision | Recall | Jaccard |
|---|---:|---:|---:|---:|---:|---:|---:|
| Successful `report your organisation` | 0 | 1 | 16 | 15 | 1.000 | 0.125 | 0.125 |
|  | 1 | 16 | 430 | 394 | 0.313 | 0.625 | 0.263 |
|  | 2 | 410 | 627 | 551 | 0.020 | 1.000 | 0.020 |
| Route-shortfall `describe who you are` | 0 | 1 | 15 | 14 | 1.000 | 0.333 | 0.333 |
|  | 1 | 15 | 426 | 394 | 0.200 | 1.000 | 0.200 |
|  | 2 | 409 | 635 | 559 | 0.007 | 1.000 | 0.007 |

The radius-1 candidate recovers all three nodes in the second prompt's operational projection, but includes 12 additional nodes. For the successful prompt it recovers only five of eight operational nodes. Radius 2 covers both operational projections while expanding to roughly 410 nodes, with precision below 2%. The declared projections are incomplete operational labels, so these scores compare graph neighborhoods with that label only; recall 1.0 is not task-dependency completeness.

The BFS itself is fast in this fixture. The runner's adjacency-build medians are 103.8 ms on the first prompt and 10.4 ms on the second, while radius-2 boundary projection medians are 596 ms and 623 ms. These timings include Python snapshot traversal and are highly implementation-specific; they are discovery/projection costs, not substrate settlement costs. For scale context, the worker's two-prompt mean call time is about 320–328 ms. Thus this naïve repeated full-edge scan already costs more than the measured mean call on this fixture; optimize or use incremental cuts only after correctness and interface completeness are established.

## Interpretation

This is a negative diagnostic for simple rooted-neighborhood framing: label coverage rises with radius, but so do frame size and crossing work, and full label recall requires a large expansion. It does not test an optimized graph partitioner, learned frame acquisition, natural-task prevalence, or task-variable interface size. Boundary attribute summaries contain types and key names only; none is verified as task-relevant. The run still lacks a complete runtime operation-dependency graph and finite interface-domain measurements.

Attempt 1 passed the runner gates but failed independent analysis because of a width-field normalization bug. Its raw capture and failed analysis are preserved and excluded; the narrow [amendment](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_AMENDMENT_20260928.md) corrected the analyzer and locked rerun. The valid result uses only the amended three-worker capture.

## Artifacts

- [Preregistration](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_PREREG_20260928.md)
- [Amendment](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_AMENDMENT_20260928.md)
- Runner: [`substrate_rooted_frame_proposal_panel_v1.py`](../../../scripts/substrate_rooted_frame_proposal_panel_v1.py)
- Independent analyzer: [`analyze_substrate_rooted_frame_proposal_panel_v1.py`](../../../scripts/analyze_substrate_rooted_frame_proposal_panel_v1.py)
- Accepted source lock: [lock JSON](../../../evaluation/substrate_capability/rooted_frame_proposal_panel_v1_lock_20260928.json)
- Accepted raw capture: [worker report](../../../evaluation/reports/rooted_frame_proposal_panel_v1_20260928.json)
- Independent analysis: [analysis JSON](../../../evaluation/reports/rooted_frame_proposal_panel_v1_analysis_20260928.json)
- Preserved attempt 1: [runner capture](../../../evaluation/reports/rooted_frame_proposal_panel_v1_attempt1_20260928.json), [analyzer failure](../../../evaluation/reports/rooted_frame_proposal_panel_v1_attempt1_analyzer_failure_20260928.json), [initial lock](../../../evaluation/substrate_capability/rooted_frame_proposal_panel_v1_attempt1_lock_20260928.json)
