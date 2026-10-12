# ProblemShape eventization component timing at N=32

**Run date:** 2026-09-25  
**Status:** preregistered exploratory diagnostic; one process per arm and workload.

## Findings

The detailed worker records separate treatment observation construction, host index/event maintenance, native rule closure, and the remaining receipt/timer residual. Candidate component shares are similar across the two workloads:

| Workload | Candidate total vs baseline total | Observation construction | Index/event maintenance | Native closure | Remaining receipt/timer residual |
|---|---:|---:|---:|---:|---:|
| Recognition-only | 815.6 ms vs 828.6 ms (ratio 0.984) | 6.90 ms (0.85%) | 1.70 ms (0.21%) | 804.1 ms (98.59%) | 2.87 ms (0.35%) |
| Recurrent residual | 777.5 ms vs 747.2 ms (ratio 1.041) | 6.76 ms (0.87%) | 1.66 ms (0.21%) | 766.2 ms (98.54%) | 2.91 ms (0.37%) |

The same workers retain large ProblemShape-only operation reductions: candidate pairs fall 84.0% / 83.7% and Term evaluations 67.1% / 65.8%, recognition / recurrent respectively. However, the aggregate audit over all rules tells a different scale story: total Term evaluations fall only 0.43% (3,048,748→3,035,788) and 0.41% (3,050,449→3,037,980); all-rule candidate tests fall 0.86% / 0.82%, `where` evaluations 0.92% / 0.92%, and rule enumerations are unchanged. ProblemShape accounted for only about 0.7% of all Term evaluations at baseline. Detailed per-rule records recover valid baseline `ps_mint` counts that prior summary wrappers omitted: 528→0 candidate pairs and 2,640→0 Term evaluations on recognition; 530→6 pairs and 2,818→116 Terms on recurrent residual. The new index/event relations double measured graph writes (129→258/259) in these worker runs.

The measured host index/event maintenance is about 1.7 ms total per 32-observation worker, roughly 0.2% of candidate observation time. It is too small by itself to explain the variable total-time difference. Nearly all elapsed time is within native closure; one recognition worker is modestly faster and one recurrent worker is slower. This is descriptive single-run evidence, not a causal conclusion: native closure covers more than just the counted ProblemShape Term evaluations, and OS/runtime variation remains uncontrolled at this sample size.

## Interpretation

The scale audit explains why large ProblemShape-only reductions need not move wall time much: the optimized rules contribute under one percent of the all-rule Term evaluations in this full-seed worker, while the dominant rule-enumeration count does not change. Host index maintenance alone is not the evident cost bottleneck. The next performance study should preserve per-step timing components in repeated paired workers and test whether changes to the global rule schedule can remove work without broad regressions. It should continue to report subsystem and all-rule counters separately.

## Scope and artifacts

One fresh process per arm/mix at N=32; the two authored workloads are not a representative task distribution. Baseline does not split observation construction and closure into separately timed intervals, so only candidate components are decomposed. No asymptotic or substrate-wide speed claim follows.

- Preregistration: [`SUBSTRATE_PROBLEM_SHAPE_EVENTIZATION_COST_ATTRIBUTION_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_EVENTIZATION_COST_ATTRIBUTION_PREREG_20260925.md)
- Runner: [`substrate_problem_shape_eventization_cost_attribution.py`](../../../scripts/substrate_problem_shape_eventization_cost_attribution.py)
- Independent analyzer: [`analyze_substrate_problem_shape_eventization_cost_attribution.py`](../../../scripts/analyze_substrate_problem_shape_eventization_cost_attribution.py)
- Input lock: [JSON](../../../evaluation/substrate_capability/problem_shape_eventization_cost_attribution_lock_20260925.json)
- Full raw worker records: [JSON](../../../evaluation/reports/substrate_problem_shape_eventization_cost_attribution_20260925.json)
- Validated analysis: [JSON](../../../evaluation/reports/substrate_problem_shape_eventization_cost_attribution_analysis_20260925.json)
