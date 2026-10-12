# Live self-report task-boundary v2.1 replication results (2026-09-27)

## Outcome

The separately locked replication passes all 51/51 analyzer checks across three fresh worker processes. Worker-start, worker-finish, control-run, and post-run source fingerprints all match the v2.1 lock. Semantic graph digest, declared task projections, event identity shape, and matcher totals reproduce exactly across workers. The five task-identity controls pass, as do independent full-edge cut recomputation and matcher attribution/conservation.

The prior v2 capture remains preserved as a source-drift-limited exploratory result. v2.1 was locked after the observed `substrate/world_adapter.py` edit and did not alter its workload, projection definition, or gates.

## Measurements

The full runtime graph contains 24,982 nodes and 11,519 typed edges. The two protocol-defined projections are:

| Projection | Owned nodes | Internal edges | Boundary incidences | Unique external nodes | Owned induced-width upper bound |
|---|---:|---:|---:|---:|---:|
| Self-report turn 0 | 8 | 16 | 36 | 19 | 2 |
| Follow-up turn 1 | 3 | 2 | 18 | 15 | 1 |

For the successful turn, selection, execution, and action-result closures each perform 8,031, 8,002, and 7,998 candidate tests; each count is identical in all workers. There are zero unattributed candidate tests. Term evaluations are 88,306, 85,311, and 85,292 for those events, also exact repeats. Median seed boot time is 12.30 seconds; median two-turn measured time is 343.23 ms, including audit instrumentation and both prompts. These timings describe this instrumented fixture only.

The second prompt reproduces the known route-selection shortfall: it creates no lifecycle Goal. It remains a negative capability control, not successful task execution.

## Interpretation and limits

This source-stable result establishes that the small protocol-owned projections and their complete typed-edge cuts are reproducible on this fixture. The boundaries are not especially sparse by incidence count: the eight-node view has 36 incidences to 19 external nodes. The width values are deterministic min-fill upper bounds for each owned induced graph. Neither result bounds the treewidth of the full inference or matcher-dependency graph.

Ownership is specified by the measurement protocol, not learned by the substrate. The capture does not demonstrate inference factorization, execution within frames, hierarchical separator composition, cheap-cut prevalence across natural tasks, or scaling with task/boundary size. Accordingly, it supports repeatable local projections and exact operation attribution, but it does not yet validate the cheap-cut tractability hypothesis.

Next measure independently sourced task families and controlled increases in owned and boundary size, then compare protocol projections with frame assignments produced by the substrate. Retain an explicit quality oracle and measure total setup-plus-execution cost so small local widths are not mistaken for a speedup.

## Reproduction

- Preregistration: [v2.1 protocol](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_1_PREREG_20260927.md)
- Amendment: [replication amendment](SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_1_AMENDMENT_20260927.md)
- Runner: [capture script](../../../scripts/substrate_live_self_report_task_boundary_v2_1.py)
- Analyzer: [analysis script](../../../scripts/analyze_substrate_live_self_report_task_boundary_v2_1.py)
- Lock: [locked inputs](../../../evaluation/substrate_capability/live_self_report_task_boundary_v2_1_lock_20260927.json)
- Raw capture: [worker data](../../../evaluation/reports/substrate_live_self_report_task_boundary_v2_1_20260927.json)
- Analysis: [integrity and summary](../../../evaluation/reports/substrate_live_self_report_task_boundary_v2_1_analysis_20260927.json)
