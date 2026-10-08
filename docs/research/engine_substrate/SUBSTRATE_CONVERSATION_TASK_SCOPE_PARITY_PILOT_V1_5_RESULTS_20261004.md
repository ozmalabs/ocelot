# Conversation task-scope parity pilot v1.5 results

Date: 2026-10-04  
Status: exploratory, source-locked capture; independent analysis passes.

## Question and method

V1.5 extends the scoped-loop trace with five matching-funnel events: successful matcher binding callbacks, bindings retained by the scope predicate, bindings rejected by it, duplicate in-scope bindings skipped by canonical-key deduplication, and distinct bindings passed to `apply_rule_full`. These boundaries count matched bindings, not graph candidates. Candidate-pair and Term-evaluation counters continue to measure matcher search volume. Three fresh workers repeat the v1.4 authored workload and exact-state comparison.

The current native engine is provenance-current (`1d00db8812fb`). The runner's nine capture checks pass. Independent analysis passes with no errors, confirms the source lock (including pinned v1.4 artifacts), all 12 paired cases and 198 checkpoint pairs, and per-checkpoint binding conservation:

- matched = in-scope + out-of-scope;
- in-scope = duplicate + apply attempts.

No work-trace rows were dropped. All paired final and checkpoint graph states match monolithic closure; task scopes quiesce without deferred effects.

## Scoped binding funnel

Totals below aggregate three workers. Duplicate counts are zero in every reported workload, so each distinct in-scope binding reached one apply attempt.

| Workload | Matched bindings | In scope | Out of scope | Apply attempts | Out-of-scope share |
|---|---:|---:|---:|---:|---:|
| Concurrent goals, 2 | 27 | 18 | 9 | 18 | 33.3% |
| Concurrent goals, 4 | 90 | 36 | 54 | 36 | 60.0% |
| Concurrent goals, 8 | 324 | 72 | 252 | 72 | 77.8% |
| Common-ground stress | 45 | 18 | 27 | 18 | 60.0% |

The out-of-scope share rises with goal count in the concurrent-goal fixtures. This identifies substantial post-match filtering in this implementation, but it is not the full wasted search cost: the filter runs after successful bindings have already been enumerated, and candidate-pair counters capture broader matcher effort. At eight goals the scoped arm still records 46,140 candidate pairs and 156,444 Term evaluations versus 4,092 and 11,184 for monolithic closure.

## Interpretation and next work

These counters show where returned bindings cross the scope boundary and where apply calls occur. They do not prove that the scope boundary is semantically complete, that excluded bindings were unnecessary under arbitrary interactions, or that the engine can learn such scopes. The fixture annotations remain explicit and symmetric; broad applicability and natural-task prevalence remain unmeasured.

Next evaluate whether an ownership-seeded matcher can avoid enumerating out-of-scope bindings while preserving exact state under cross-frame/shared-state mutation controls. Charge scope discovery, candidate construction, and closure work. Expand to independent task families before using this funnel as evidence for a general tractability claim.

Artifacts: [preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_5_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5.py), [analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_5.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5_lock_20261004.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_5_20261004.json), and [independent analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_5_analysis_20261004.json).
