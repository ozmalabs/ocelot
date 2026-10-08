# Connected discourse task graph and access census results

**Run:** 2026-09-26. **Grade:** fresh-process diagnostic on one authored connected task; not a representative natural-task estimate. The fixture has prior mechanism-test use. Event grouping was frozen from its `origin` and `unsolicited` relations before this capture.

## Structural result

The ten-event mixed dialogue produced three fixture-derived frames of sizes 5, 1, and 6 (event plus goal nodes). The native graph ended with 261 nodes and 235 edges, of which 12 event/goal nodes were assigned to frames. Two direct graph edges cross frame boundaries, both `follows_event`. Five unassigned boundary nodes have 40 incident edges to frame nodes. The shared discourse-state node touches all three frames, so the frame interaction graph is a triangle and has exact treewidth 2. This width is for the three-frame interaction projection induced by the declared frame and boundary rule; it is not the treewidth of the full substrate graph or a general rule-dependency graph.

## Native execution and trace

Native closure was run after every event. Across ten checkpoints it made six progressing rule applications, enumerated 135 candidate pairs, and evaluated 558 Terms. All checkpoints reached a fixed point. The two goals resolved with transition provenance local to their own frames, the expected common-ground claims were preserved, and all three fresh processes produced identical graph state at every checkpoint.

The partial access trace records 193 events across the three discourse lifecycle rules, with no dropped events. It records no direct trace row whose two concrete endpoints belong to different task frames. This does not imply no cross-frame dependency: the graph has direct `follows_event` edges across frames, and all frames share the discourse-state boundary. The three rules have no wildcard read/write flags in their native static access summaries; that is useful on this path but does not establish completeness of the trace model.

The task and common-ground oracles pass. A contrast with the preceding all-at-once diagnostic is instructive: materializing the complete future event graph before closure made early goals consume later events. This runner corrects the sequence by materializing and settling each event before the next exists. The earlier failed attempt was overwritten during development and is not included as a raw record; the corrected procedure and its incremental construction are frozen in the runner.

## Claim boundary

This is a connected task-derived structural panel, not a frame-local execution result. It supports measuring event boundaries through a shared state node and quantifies their interaction width on this fixture. It does not run partitioned closure, measure partition construction/update cost, test notifications, or estimate how often natural conversations have similar structure. Per-checkpoint times are single-run diagnostics and are not performance estimates.

All 14 runner checks and 12 independent analyzer checks pass. See the [preregistration](SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_PREREG_20260926.md), [runner](../../../scripts/substrate_discourse_connected_task_census_v1.py), [independent analyzer](../../../scripts/analyze_substrate_discourse_connected_task_census_v1.py), [input lock](../../../evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json), and [analysis](../../../evaluation/reports/substrate_discourse_connected_task_census_v1_analysis_20260926.json).
