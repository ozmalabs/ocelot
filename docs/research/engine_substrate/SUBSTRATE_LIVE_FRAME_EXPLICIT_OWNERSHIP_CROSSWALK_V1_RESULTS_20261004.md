# Live frame explicit-ownership crosswalk v1 results

The source-locked two-request graph contains 25,065 nodes and 11,543 edges.
Reconstructing a conservative relation projection from each prompt Message,
explicit `comprehends` Goal links, and the Goal's `origin_event`/`for_goal`
DiscourseEvents yields five nodes for turn 0 and one node for turn 1. The
protocol-supplied operational cuts contain eight and three nodes. All projected
nodes are included in their corresponding operational cuts (recall 1.0), while
operational precision is 0.625 and 0.333; Jaccard is 0.625 and 0.333. The
operational-only nodes are one Message, one DiscourseEvent, and one
ProductionGateReceipt on turn 0, and one Message plus one DiscourseEvent on
turn 1. There are no nodes shared between operational cuts and two direct
cross-cut graph edges.

This shows that prompt/Goal/Event relations account for only part of the
operational ownership sets in this sequence. The operational cut includes
additional lifecycle artifacts, and two cross-cut edges remain despite distinct
owner sets. Neither side is a complete dependency specification: the explicit
projection is conservative, and the operational mapping is harness-supplied.
The cut sizes and induced-subgraph treewidth bounds therefore do not prove
factorization, learned frame locality, or cheap inference. This is one authored
self-report sequence; independent human ownership labels and additional
multi-task graphs are still needed.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_LIVE_FRAME_EXPLICIT_OWNERSHIP_CROSSWALK_V1_PREREG_20261004.md)
- [Analyzer](../../../evaluation/substrate_capability/analyze_live_frame_explicit_ownership_crosswalk_v1.py)
- [Capture summary](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json)
- [Raw capture](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz)
- [Crosswalk analysis](../../../evaluation/reports/live_frame_explicit_ownership_crosswalk_v1_20261004.json)

Run `python3 evaluation/substrate_capability/analyze_live_frame_explicit_ownership_crosswalk_v1.py` from the repository root.
