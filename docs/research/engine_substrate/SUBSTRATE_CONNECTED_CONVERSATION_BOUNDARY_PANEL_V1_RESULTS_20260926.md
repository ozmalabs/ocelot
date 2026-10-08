# Connected conversation boundary panel results

## Result

The 12-case panel passed its runner and independent-analysis gates across three fresh processes. It covers one authored ten-event common-ground stress fixture and generated same-addressee concurrent-goal cases at N=2/4/8. All event closures reached native fixed points; all Goals resolved with the intended three transition events; graph digests and per-checkpoint work counters reproduced exactly across workers. The analyzer independently rebuilt frame ownership, direct cross-frame edges, boundary-node incidences, interaction projections, and exact treewidth.

The common-ground fixture yields four frames sized 5/1/1/5, five direct cross-frame edges, five shared boundary nodes with 14 incidences, and interaction-projection treewidth 3. In the generated scale family, N=2/4/8 produces 2/4/8 frames of five owned nodes each. Direct cross-frame edges rise 3/7/15, and shared boundary incidence rises 8/16/32. The specified interaction projection has exact treewidth 1/3/7. That projection completes each pair of frames touched by the same global boundary node; it is a conservative pairwise graph view of a shared bus, not evidence for independent pairwise factors between all frames.

Global closure work rises from 119 to 386 to 1,364 candidate pairs and from 404 to 1,160 to 3,728 Term evaluations for N=2/4/8. Process peak RSS medians are 37.2/37.8/38.5 MiB; these process-level values are import-dominated and not native allocation attribution. This is a structural/work census, not a partitioned-closure or speedup result.

## Limits

The common-ground fixture is one authored sequence; the concurrent-goal scale cases are generated stress workloads. This is not a representative distribution of natural conversations. The frame assignment follows fixture origins/independent markers and explicit `for_goal` identity, and shared bus nodes create projection cliques. No learned partition, runtime cut discovery, native boundary messages, or end-to-end locality benefit is measured. A direct next step is to retain hyperedge/shared-variable structure in a boundary representation and measure additional independently authored tasks before estimating a workload distribution.

The initial worker launch failed at JSON serialization after materializing cases; the failure record is preserved. The independent analyzer's first attempt compared list indices to `range` objects and failed its lifecycle gate; that verifier failure is also preserved. The fixed runner and analyzer pass the full panel.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_CONNECTED_CONVERSATION_BOUNDARY_PANEL_PREREG_20260926.md)
- Runner: [`substrate_connected_conversation_boundary_panel_v1.py`](../../../scripts/substrate_connected_conversation_boundary_panel_v1.py)
- Independent analyzer: [`analyze_substrate_connected_conversation_boundary_panel_v1.py`](../../../scripts/analyze_substrate_connected_conversation_boundary_panel_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_connected_conversation_boundary_panel_v1_analysis_20260926.json)
- Preserved worker serialization failure: [failure record](../../../evaluation/reports/substrate_connected_conversation_boundary_panel_v1_serialization_failure_20260926.json)
- Preserved analyzer failure: [failure capture](../../../evaluation/reports/substrate_connected_conversation_boundary_panel_v1_analyzer_failure_20260926.json)
