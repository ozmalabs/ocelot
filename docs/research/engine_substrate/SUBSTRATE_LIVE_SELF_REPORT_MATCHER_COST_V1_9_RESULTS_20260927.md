# Live self-report matcher cost v1.9 results

Date: 2026-09-27 local

## Outcome

The source/native lock stayed stable across three fresh processes and the five established identity/failure controls passed. The organization prompt reached the live self-report route, created and resolved its own Goal, and emitted exactly `selection`, `execution`, and `action_result`. The second prompt reproduced the known route-selection shortfall: it returned a nonempty answer but had no self-report route, Goal, or lifecycle producer work. The two prompts are therefore analyzed separately.

The independent analyzer passes **72/72 gates**, including exact candidate attribution at each of the nine producer-event intervals. Every candidate test maps to a non-ambiguous native matcher identity and valid match clause. Verified per-rule and per-clause counts each conserve to global `cand_tested`; unattributed work is zero in all intervals. Term evaluation counts reconcile as well.

## Work measured per worker

| Producer event | Candidate tests | Term evaluations | Median instrumented elapsed time |
|---|---:|---:|---:|
| Selection | 8,031 | 88,306 | 13.59 ms |
| Execution | 8,002 | 85,311 | 12.55 ms |
| Action result | 7,998 | 85,292 | 13.35 ms |
| **Three event closures** | **24,031** | **258,909** | — |

Across the three workers, one-edge matchers account for 84.51% of verified candidate tests; two-edge matchers 11.92%; all larger arities together 3.57%. `curiosity_targets_ambivalent_nodes` is the largest named matcher contributor in each event closure. These are native operation counts and audit-on event timings for one held self-report route, not uninstrumented latency, natural-task frequency, or a general cost guarantee.

## Interpretation

This is an independent task topology from attached-scene `describe_scene`. It shows that the v1.3 native matcher attribution path transfers to a second live route and preserves exact count conservation. It does not establish that the world generally has cheap separators, that matching scales polynomially on natural tasks, or that Rung 3/4 induction is tractable. The repeatable second-prompt route-selection shortfall remains an open capability item.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_SELF_REPORT_MATCHER_COST_V1_9_PREREG_20260927.md)
- [Implementation amendment](SUBSTRATE_LIVE_SELF_REPORT_MATCHER_COST_V1_9_AMENDMENT_20260927.md)
- [Source/native lock](../../../evaluation/substrate_capability/live_self_report_matcher_cost_v1_9_lock_20260927.json)
- [Three-worker capture](../../../evaluation/reports/substrate_live_self_report_matcher_cost_v1_9_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_live_self_report_matcher_cost_v1_9_analysis_20260927.json)
- [Runner](../../../scripts/substrate_live_self_report_matcher_cost_v1_9.py) and [analyzer](../../../scripts/analyze_substrate_live_self_report_matcher_cost_v1_9.py)
