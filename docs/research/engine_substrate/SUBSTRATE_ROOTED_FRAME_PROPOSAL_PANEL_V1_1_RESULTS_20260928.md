# Rooted frame-proposal panel v1.1 results (2026-09-28)

## Outcome

The amended three-worker capture passes all 10 runner checks and five semantic/control checks. The native access trace is nonempty for both prompts, has zero dropped event keys, and reconciles exactly to its weighted event rows. Source locks are stable through workers and controls. Candidate sets, boundaries, trace projections, and graph semantics reproduce across all three workers. The final graph has 25,021 nodes and 11,548 edges; the traced and untraced v1 baseline semantic graph digests are identical.

The independent analyzer passes all 11 gates. It independently rebuilds all 18 BFS sets and cuts from the structural snapshots, then recomputes each trace-to-candidate projection from concrete event rows. This validates the selected trace projection, not trace completeness. The native trace records only selected event sites while a `RuleUid` is active; host work, scheduler work outside rules, failed matcher bindings, and other documented blind spots remain outside this measurement ([trace coverage audit](SUBSTRATE_RUNTIME_ACCESS_TRACE_COVERAGE_AUDIT_V1_RESULTS_20260926.md)).

## Structural and traced-work results

Each request emits the same trace in all three workers: 333,433 weighted events in 57,475 rows for the successful prompt, and 79,966 weighted events in 15,672 rows for the route-shortfall prompt. No trace rows were dropped.

| Prompt | Radius | Proposed nodes | Cut incidences | Distinct external nodes | Label recall | Label precision | Weighted trace events touching candidate | Share of selected trace |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Successful `report your organisation` | 0 | 1 | 16 | 15 | 0.125 | 1.000 | 1,543 | 0.46% |
|  | 1 | 16 | 430 | 394 | 0.625 | 0.313 | 9,387 | 2.82% |
|  | 2 | 410 | 627 | 551 | 1.000 | 0.020 | 19,990 | 6.00% |
| Route-shortfall `describe who you are` | 0 | 1 | 15 | 14 | 0.333 | 1.000 | 620 | 0.78% |
|  | 1 | 15 | 426 | 394 | 1.000 | 0.200 | 2,861 | 3.58% |
|  | 2 | 409 | 635 | 559 | 1.000 | 0.007 | 9,641 | 12.06% |

The table reports recorded node/peer events with at least one endpoint in the proposed frame. Type/resource-only events without concrete node IDs are tallied separately. The successful prompt has 27 weighted events with no concrete node IDs; the route-shortfall prompt has none. At radius 2, the proposal reaches every protocol-owned node but touches only 6.00% and 12.06% of selected events respectively. This is a concrete warning that topological proximity to an input node is a weak proxy for recorded operation scope. Events outside a proposal may be irrelevant scans, shared dependencies, broad matcher work, or missing task-frame members; this experiment does not adjudicate necessity.

## Cost and limits

The radius-2 boundary projection took median 609 ms and 609 ms for the two prompts in this Python implementation; BFS expansion itself was about 24 microseconds. The total two-prompt caller time median is about 321 ms under the instrumented runner. These timing boundaries are not comparable baseline CPU measurements: native tracing and lifecycle scale auditing are active, and the cut routine rebuilds edge structures and computes induced width. They do show that this straightforward cut-discovery implementation is currently expensive enough to erase any hypothesized cheap-operation advantage on this fixture.

The operational task labels remain protocol-defined and incomplete. The native trace is partial, it does not capture Python host effects or all failed matcher/scheduler work, and the fixture is one authored task family. Therefore this result does not establish task-relevant interface size, complete dependency coverage, correctness of frame-localized execution, learned framing, or natural-task prevalence. The first `v1.1` capture passed runner gates but its independent analyzer had a zero-field normalization defect; it is preserved as attempt 1 and excluded. [Amendment v1.2](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_2_AMENDMENT_20260928.md) records the repair and fresh accepted rerun.

## Artifacts

- Base design: [v1 preregistration](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_PREREG_20260928.md)
- Trace extension: [v1.1 amendment](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_1_AMENDMENT_20260928.md)
- Analyzer repair: [v1.2 amendment](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_2_AMENDMENT_20260928.md)
- Runner: [`substrate_rooted_frame_proposal_panel_v1_1.py`](../../../scripts/substrate_rooted_frame_proposal_panel_v1_1.py)
- Independent analyzer: [`analyze_substrate_rooted_frame_proposal_panel_v1_1.py`](../../../scripts/analyze_substrate_rooted_frame_proposal_panel_v1_1.py)
- Source lock: [accepted lock](../../../evaluation/substrate_capability/rooted_frame_proposal_panel_v1_1_lock_20260928.json)
- Raw capture: [accepted report](../../../evaluation/reports/rooted_frame_proposal_panel_v1_1_20260928.json)
- Independent analysis: [analysis JSON](../../../evaluation/reports/rooted_frame_proposal_panel_v1_1_analysis_20260928.json)
- Excluded attempt 1: [raw report](../../../evaluation/reports/rooted_frame_proposal_panel_v1_1_attempt1_20260928.json), [failed analysis](../../../evaluation/reports/rooted_frame_proposal_panel_v1_1_attempt1_analyzer_failure_20260928.json), [lock](../../../evaluation/substrate_capability/rooted_frame_proposal_panel_v1_1_attempt1_lock_20260928.json)
