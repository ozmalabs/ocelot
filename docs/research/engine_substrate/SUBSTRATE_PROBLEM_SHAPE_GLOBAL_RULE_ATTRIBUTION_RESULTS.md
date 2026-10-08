# ProblemShape eventization: global rule attribution at N=32

**Run date:** 2026-09-25  
**Status:** preregistered exploratory paired counter/timing analysis.

## Semantic and process gates

Six fresh-process baseline/candidate pairs ran for each of two authored workloads, recognition-only and recurrent-residual (24 workers total). All 12 pairs passed their worker fixed-point/status/mint gates and paired transition parity. Every pair used unique worker PIDs; arm order was balanced three baseline-first and three candidate-first within each workload. Full per-rule rows are retained in raw worker records. Per-rule candidate-pair and Term counts were stable across the six workers per arm.

## Subsystem versus whole-engine work

| N=32 workload | ProblemShape pairs, baseline → candidate | ProblemShape Terms, baseline → candidate | All-rule Terms, baseline → candidate | All-rule candidate tests | All-rule `where` evaluations | Rule enumerations |
|---|---:|---:|---:|---:|---:|---:|
| Recognition-only | 3,696 → 592 (−84.0%) | 21,616 → 7,120 (−67.1%) | 3,048,748 → 3,035,788 (−0.43%) | 324,976 → 322,192 (−0.86%) | 312,592 → 309,712 (−0.92%) | median 96,064 in both arms |
| Recurrent-residual | 3,707 → 606 (−83.7%) | 22,135 → 7,572 (−65.8%) | 3,050,449 → 3,037,980 (−0.41%) | 323,692 → 321,035 (−0.82%) | 310,389 → 307,543 (−0.92%) | median 96,897 in both arms |

The large relative reduction inside ProblemShape translates to less than a half-percent reduction in all-rule Term evaluations. Per-rule readback identifies increased candidate pairs and Term evaluations in six other rules. In recognition, each of `ca_mark_cut`, `ca_step_mag`, and `ca_step_res` rises from 64 to 128 candidate pairs and 320 to 640 Terms; `retire_duplicate_residual_concern` rises 32→64 pairs / 320→640 Terms, while each of `resolve_reply_fix_gap` and `resolve_self_account_gap` rises 32→64 / 128→256. Recurrent-residual shows the same pattern: the `ca_*` trio is 66→130 pairs / 330→650 Terms; `retire_duplicate_residual_concern` is 65→128 / 650→1,280; and each resolve rule is 65→128 / 260→512. These increases add 1,536 / 2,094 Terms respectively and offset part of the ProblemShape reduction.

Enumeration counts for the six affected rules are unchanged, and all paired global enumeration totals match exactly. Their candidate expansion work therefore increases within the same number of enumerations. Global enumeration totals vary by 32 across workers (one per observation); this variation is retained, and the paired baseline/candidate totals match for every pair. The records establish co-occurring count changes; they do not establish the precise causal path from experimental graph changes to those expanded candidate sets.

Measured graph writes rise from 129 to 259 in recognition and 129 to 258 in recurrent-residual as the treatment installs and updates its event/index relations.

## Timing

| Workload | Median candidate/baseline wall ratio | Paired bootstrap 95% interval | Candidate faster |
|---|---:|---:|---:|
| Recognition-only | 0.963 | 0.933–1.073 | 4/6 |
| Recurrent-residual | 1.014 | 0.944–1.102 | 2/6 |

Both intervals include parity. The counts show targeted work avoidance, but do not show a reliable runtime gain on the full seeded engine. This is consistent with the small share of total Term evaluations affected, though six pairs per mix are not enough to estimate small effects precisely.

## Interpretation

This result sharpens the tractability evidence: eventization saves substantial work in its target rule family, but global closure still enumerates the same number of rule slots and several other rules do additional candidate work. The next engine step is to inspect the relation populations and rule match joins behind these six candidate-pair increases before testing a scheduler/filter change. Any optimization must use exact-state and all-rule attribution gates and preserve unaffected workloads as controls. A per-rule delta is diagnostic evidence, not authorization to suppress another rule.

## Scope and artifacts

Two authored N=32 workloads only; not natural-task prevalence, asymptotic complexity, or substrate-wide performance. Timing is exploratory. The all-rule audit fields were added to the worker readback for this run; the locked worker hashes capture that instrumentation revision.

- Preregistration: [`SUBSTRATE_PROBLEM_SHAPE_GLOBAL_RULE_ATTRIBUTION_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_GLOBAL_RULE_ATTRIBUTION_PREREG_20260925.md)
- Runner: [`substrate_problem_shape_global_rule_attribution.py`](../../../scripts/substrate_problem_shape_global_rule_attribution.py)
- Independent analyzer: [`analyze_substrate_problem_shape_global_rule_attribution.py`](../../../scripts/analyze_substrate_problem_shape_global_rule_attribution.py)
- Input lock: [JSON](../../../evaluation/substrate_capability/problem_shape_global_rule_attribution_lock_20260925.json)
- Full raw paired workers: [JSON](../../../evaluation/reports/substrate_problem_shape_global_rule_attribution_20260925.json)
- Validated analysis: [JSON](../../../evaluation/reports/substrate_problem_shape_global_rule_attribution_analysis_20260925.json)
