# Live describe-scene operation-work trace v2.7 results

**Status:** source-stable paired capture passes; the locked offline analyzer had a syntax defect, disclosed and corrected in the analysis amendment.

## Gates

All 12 runner gates pass across three traced/untraced pairs and six fresh worker processes. Sources match the lock at worker start, worker end, and post-run. Threads join without errors; the task, schedule, lifecycle and reply checks pass; each pair has exact semantic and whole-graph parity; request access/work snapshots are complete; work counters reconcile; no access or work events are dropped; and both untraced streams are empty. The independent corrected analysis passes all nine checks against the immutable capture, including current native kind definitions.

## Scheduler/deferred work

Each of the three traced processes produces identical per-request counters:

| Request | Operations | Rows | Scheduler passes | Selected-rule slots | Dirty-vector slots | External-poll slots | Fixed-point-probe slots |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 21 | 126 | 37 | 54,371 | 87,734 | 87,734 | 1,172 |
| B | 13 | 78 | 24 | 37,442 | 57,096 | 57,096 | 1,045 |

All work rows have producer UID 0, meaning they were recorded outside an active rule context. `operation_kind` contributes 21 and 13 rows, one per operation. Dirty-vector slots, external-poll slots, selected-rule slots, and fixed-point probes are distinct instrumentation counters with their own units. The row-unit sums (231,069 for A and 152,716 for B) are convenient reconciliation totals only; they are not a single dimensionally meaningful work measure, and must not be compared to time or machine cycles.

This confirms that native scheduler/deferred counters can be captured and attributed to the serialized request interval. It does not show how much of that work is necessary, how it scales with task size, or which request-owned frame caused it. UID 0 attribution is insufficient for a locality claim. No size axis was varied, so there is no asymptotic or commodity-scale conclusion.

## Analysis source correction

The capture itself passed its 12 in-run gates. After the capture, the separately locked analyzer failed to parse because of one indentation error. Its exact locked bytes are retained and match the lock hash; the corrected standalone reanalyzer passes nine checks and its source hash is stored in the analysis JSON. This is a post-capture analysis correction, not a change to worker data. See the [analysis amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_OPERATION_WORK_V2_7_ANALYSIS_AMENDMENT_20260929.md); future locks must syntax-check all listed scripts before execution.

## Next gate

Vary request-owned task size and matched global/distractor populations while preserving the task oracle. Capture these work counters alongside candidate-test and Term-evaluation counts and run costs; reconcile them with per-rule/scoped work and node ownership. Then compare request-partitioned execution against full closure with exact whole-graph parity and omission/contamination controls. Repeat on a second production family before estimating natural locality prevalence.

## Artifacts

- Protocol: [v2.7 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_OPERATION_WORK_V2_7_PREREG_20260929.md); amendment: [analysis correction](SUBSTRATE_LIVE_DESCRIBE_SCENE_OPERATION_WORK_V2_7_ANALYSIS_AMENDMENT_20260929.md).
- Capture runner: [v2.7](../../../scripts/substrate_live_describe_scene_operation_work_v2_7.py); corrected analyzer: [v2.7](../../../scripts/analyze_substrate_live_describe_scene_operation_work_v2_7.py); locked analyzer source: [preserved bytes](../../../scripts/analyze_substrate_live_describe_scene_operation_work_v2_7_locked_source.py).
- Lock: [source lock](../../../evaluation/substrate_capability/live_describe_scene_operation_work_v2_7_lock_20260929.json); capture: [summary](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_7_20260929.json), [raw workers](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_7_workers_raw_20260929.json); analysis: [work report](../../../evaluation/reports/substrate_live_describe_scene_operation_work_v2_7_analysis_20260929.json).
