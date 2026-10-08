# Current-source connected discourse task census v2.1 (2026-09-26)

## Question and lineage

V2 is a source-locked fresh-process run of the existing ten-event connected-dialogue fixture using the current Goal-identity rules. Its graph and counter replication gates passed, but its lifecycle oracle failed: the fixture adapter directly wrote selection/execution/result events without a Goal link, so the native guarded rules correctly left both Goals proposed. The failed v2 raw capture and analysis are preserved.

The amended v2.1 run sends those six lifecycle events through the existing production `domains.conversation_action._record_live_goal_event` helper. The harness supplies the inbound Message envelope the helper expects; the helper creates the explicitly goal-bound events and invokes native closure. Helper-triggered work is captured separately from ordinary per-event `run_rules_report` closure. The runner lock covers the helper, seed, materializer, fixture, runner, analyzer, native build, and relevant Rust sources.

## Correctness and replication

Three fresh processes (plain, runtime trace, repeat) pass all runner gates. The independent analyzer passes 12 structural, provenance, task, boundary, and trace checks; the separate work-attribution analyzer passes 59 lock, per-rule counter, Term-conservation, and cross-arm replication checks. All three final graphs and per-event counter profiles match. Both Goals reach `resolved`; transitions are attributed to their own task sequences at event indices 1–3 and 6–8. The runtime access trace drops no events and records no cross-frame endpoint pair for this fixture.

## Structure and work

The resulting graph contains 263 nodes and 243 directed edges. Twelve event/Goal nodes are assigned to three fixture frames of sizes 5, 1, and 6. Two direct cross-frame `follows_event` edges and 40 frame-to-global boundary incidences induce a triangle interaction graph of exact width 2. Seven unowned nodes touch frame nodes. This describes the fixture's declared partition, not a general locality guarantee.

Across all six production lifecycle helper calls and ten ordinary event settles, the counter reanalysis records 97 candidate-pair visits and 316 Term evaluations per run. The ordinary settle reports alone account for 8/32; the production helper closures account for the remaining 89/284, so reporting only the outer closure would substantially undercount work. Attribution by fixture event frame is:

| Frame | Candidate pairs | Term evaluations |
|---:|---:|---:|
| 0 | 41 | 158 |
| 1 | 0 | 0 |
| 2 | 56 | 158 |

These counters are engine work units, not CPU instructions. Timing and RSS are retained as descriptive capture values; this one fixture does not support a stable speed, memory, or scaling estimate.

## Interpretation and next gate

The v2 failure was informative: a rule-level identity guard cannot create the producer's missing identity relation, and the old fixture adapter was not exercising the live event owner. V2.1 demonstrates that the existing production helper can emit the required relation and complete two sequential lifecycles on this task fixture. It does not show that ordinary production conversations reach this helper at a representative rate, nor that frames are naturally local. The same fixture and same three arms are not independent workload samples.

Next measure the live action route with independently authored request/evidence families and multiple interleaved Goals, retaining separate attribution for event producers, lifecycle closures, and ordinary settlement. Lock exact active rules and the native artifact for every family; record whole-graph, task-owned, and boundary structure separately. Do not compare v1 and v2.1 work counts as a causal speedup because their source schemas and event producers differ.

## Reproduction artifacts

- V2.1 amendment and failed v2 disposition: [amendment](SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_V2_1_AMENDMENT_20260926.md)
- V2.1 source-locking protocol: [protocol](SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_V2_PREREG_20260926.md)
- Runner: [`substrate_discourse_connected_task_census_v2_1.py`](../../../scripts/substrate_discourse_connected_task_census_v2_1.py)
- Independent analyzer: [`analyze_substrate_discourse_connected_task_census_v2_1.py`](../../../scripts/analyze_substrate_discourse_connected_task_census_v2_1.py)
- Combined work attribution: [`analyze_substrate_discourse_connected_task_census_v2_1_work.py`](../../../scripts/analyze_substrate_discourse_connected_task_census_v2_1_work.py)
- Source lock: [v2.1 lock](../../../evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json)
- Raw capture: [three-process capture](../../../evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json)
- Analyses: [structural/task analysis](../../../evaluation/reports/substrate_discourse_connected_task_census_v2_1_analysis_20260926.json), [combined work analysis](../../../evaluation/reports/substrate_discourse_connected_task_census_v2_1_work_attribution_20260926.json)
- Preserved v2 failure: [raw capture](../../../evaluation/reports/substrate_discourse_connected_task_census_v2_20260926.json), [analysis](../../../evaluation/reports/substrate_discourse_connected_task_census_v2_analysis_20260926.json)
