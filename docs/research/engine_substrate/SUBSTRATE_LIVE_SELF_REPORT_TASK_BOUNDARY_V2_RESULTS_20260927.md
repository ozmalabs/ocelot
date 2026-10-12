# Live self-report task-boundary v2 results (2026-09-27)

## Outcome

The capture produced three fresh-process workers with identical semantic runtime graphs and identical task projections. The worker-start and worker-finish source fingerprints match the preregistered lock in all three workers. After the capture, `substrate/world_adapter.py` changed, so the post-run source fingerprint differs from the lock. The strict whole-capture provenance gate therefore fails; this is a source-drift-limited exploratory result, not a fully source-stable confirmatory result. No source was relocked after observing outcomes.

All five identity controls pass, and the independent full-edge recomputation validates the induced and cut edge lists. Native matcher attribution and counter conservation pass for all three measured producer events in all workers.

## Measurements

The full graph has 24,982 nodes and 11,519 typed edges. The two protocol-defined task projections are:

| Projection | Owned nodes | Internal edges | Boundary incidences | Unique external nodes | Owned induced width upper bound |
|---|---:|---:|---:|---:|---:|
| Self-report turn 0 | 8 | 16 | 36 | 19 | 2 |
| Follow-up turn 1 | 3 | 2 | 18 | 15 | 1 |

For turn 0, selection, execution, and action-result closures each perform 8,031, 8,002, and 7,998 candidate tests respectively; the three-worker counts are exact repeats. Each event has zero unattributed candidate tests. Term evaluations are 88,306, 85,311, and 85,292 respectively, also repeated exactly.

The follow-up turn deliberately reproduces the known route-selection shortfall: it creates no lifecycle Goal. It is included as a negative capability control, not counted as successful task execution.

## Interpretation and limits

These numbers establish small operational projections and stable matcher accounting for this one live self-report fixture. The task ownership rule is protocol-declared; it is not a frame learned by the substrate. The reported width is a min-fill upper bound on the owned induced graph only. Boundary incidence and unique external-node counts are reported separately because a small internal width does not imply a low-information boundary. The measurement does not establish exact inference factorization, full matcher dependency treewidth, a bound on frame hierarchy width, or cheap-cut prevalence across natural tasks. The 24,982-node whole graph alongside 8-node and 3-node projections also makes clear that projection size is not total runtime working-set size.

The strict analyzer reports 49/51 checks: structural integrity, repeatability, identity controls, and matcher attribution pass; the two source-stability checks fail due to the post-capture `world_adapter.py` change. Re-run from a new lock for confirmatory use. Next measure several independently sourced task families, vary owned and boundary size under a fixed protocol, and compare operational projections against learned frame assignments before claiming tractability from locality.

## Reproduction

- Preregistration: [protocol](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_PREREG_20260927.md)
- Amendment: [source and projection clarification](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_AMENDMENT_20260927.md)
- Runner: [capture script](../../../scripts/substrate_live_self_report_task_boundary_v2.py)
- Analyzer: [analysis script](../../../scripts/analyze_substrate_live_self_report_task_boundary_v2.py)
- Lock: [locked inputs](../../../evaluation/substrate_capability/live_self_report_task_boundary_v2_lock_20260927.json)
- Raw capture: [worker data](../../../evaluation/reports/substrate_live_self_report_task_boundary_v2_20260927.json)
- Analysis: [integrity and summary](../../../evaluation/reports/substrate_live_self_report_task_boundary_v2_analysis_20260927.json)
