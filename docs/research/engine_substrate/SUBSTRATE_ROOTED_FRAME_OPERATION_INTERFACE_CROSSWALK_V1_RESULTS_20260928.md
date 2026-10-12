# Rooted-frame operation-interface crosswalk v1 results

**Date:** 2026-09-28  
**Status:** all offline integrity and reconstruction gates pass; one authored prompt pair only.

## Result

The crosswalk joins the accepted rooted-frame proposal capture to the corrected static/dynamic access-scope replay. Both input analyzers pass, both raw source locks are stable, and all three worker pairs have identical whole-graph semantic digests. The analyzer independently reconstructs the radius 0/1/2 BFS sets and typed-edge cut counts from each saved graph snapshot. All 24 frame records (three workers × two prompt positions × three candidate radii, plus two reference frames per worker) pass the join and reconstruction checks.

The measured prompt pair is `report your organisation` (successful route) and `describe who you are` (route shortfall). Median across three workers:

| Prompt | Frame | Nodes | Selected trace events touching frame | Share of weighted trace | RuleUID footprints spanning frame boundary | Observed crossing edge events | Static read/write keys on spanning rules |
|---|---|---:|---:|---:|---:|---:|---:|
| Successful | Operational reference | 8 | 2,382 | 0.72% | 91 | 448 | 224 / 191 |
| Successful | BFS radius 0 | 1 | 1,543 | 0.46% | 21 | 422 | 63 / 77 |
| Successful | BFS radius 1 | 16 | 9,371 | 2.82% | 126 | 3,970 | 303 / 291 |
| Successful | BFS radius 2 | 410 | 19,934 | 5.99% | 51 | 3,518 | 122 / 156 |
| Route shortfall | Operational reference | 3 | 620 | 0.78% | 61 | 108 | 160 / 137 |
| Route shortfall | BFS radius 0 | 1 | 620 | 0.78% | 61 | 108 | 160 / 137 |
| Route shortfall | BFS radius 1 | 15 | 2,848 | 3.56% | 151 | 654 | 296 / 259 |
| Route shortfall | BFS radius 2 | 409 | 9,595 | 12.01% | 49 | 643 | 122 / 129 |

The successful radius-2 proposal covers all protocol-owned nodes but includes 410 state nodes and touches only 5.99% of the selected trace. The route-shortfall radius-2 candidate covers the operational nodes while touching 12.01%. The fraction is not a measure of task-work recall: the trace has documented blind spots, and many recorded operations may be unrelated to the task. The 49–51 RuleUIDs whose observed concrete node footprints span the radius-2 candidate also show that state-graph proximity alone does not isolate operation scopes.

## What counts as interface evidence here

The analyzer separates state-graph crossing edges, concrete traced edge accesses across the candidate boundary, static read/write resource keys on rules whose concrete trace footprint spans the cut, wildcard declarations, and outside-node attribute accesses for those rules. Unlocated events remain unknown. This is more informative than node-cut cardinality alone, but it is still not the task-relevant finite interface in the tractability contract: static keys can be wildcarded, attribute domains are not established, missing trace events cannot be treated as independence, and observed cross-boundary work is not proof that a dependency is necessary.

## Reproduction and scope

Run `python3 scripts/analyze_substrate_rooted_frame_operation_interface_crosswalk_v1.py` from the repository root. Inputs and protocol/amendment/analyzer SHA-256 digests are recorded in the [analysis JSON](../../../evaluation/reports/rooted_frame_operation_interface_crosswalk_v1_20260928.json); the [protocol](SUBSTRATE_ROOTED_FRAME_OPERATION_INTERFACE_CROSSWALK_V1_PREREG_20260928.md), [schema correction amendment](SUBSTRATE_ROOTED_FRAME_OPERATION_INTERFACE_CROSSWALK_V1_AMENDMENT_20260928.md), and [analyzer](../../../scripts/analyze_substrate_rooted_frame_operation_interface_crosswalk_v1.py) are linked directly.

This is an offline reanalysis of one authored two-prompt family, not a new capture or independent task sample. It does not show that the BFS candidate is learned, that its interface is complete, or that partitioned execution preserves fixed points. Next use a separately selected live task family with task-relevant state-variable/domain metadata, complete host/scheduler attribution, and stale/omitted-boundary mutation controls; measure partition discovery and exact partitioned-versus-monolithic execution cost.
