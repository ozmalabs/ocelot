# Conversation task-scope parity pilot v1.3 results

Date: 2026-10-03  
Status: exploratory, source-locked capture; independent analysis passes.

## Question and method

This pilot repeats the v1.2 exact-state comparison with three fresh workers and adds native operation-work rows plus scale-audit counters. It compares monolithic closure against exhaustive global resweeps of explicitly annotated task scopes for authored 2-, 4-, and 8-goal cases and a four-frame common-ground stress case. Scope roots and ownership edges are inserted symmetrically as measurement scaffolding.

The source lock covers the runner, analyzer, preregistration, prior v1.2 artifacts, conversation materializer/seed/fixtures, native extension/build manifest, and six Rust files including `term.rs`. All runner checks pass. The independent analyzer passes with no errors: 12/12 paired cases preserve final graph digests, all 198 checkpoint pairs match, goal states agree, and partition scopes report zero-progress quiescence with no deferred effects. Work-trace drops are zero.

## Measured work

| Concurrent goals | Monolithic candidate pairs | Scoped sweep candidate pairs | Ratio | Monolithic Term evaluations | Scoped sweep Term evaluations | Ratio | Scoped calls |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 357 | 1,107 | 3.10× | 1,212 | 4,041 | 3.33× | 42 |
| 4 | 1,158 | 6,750 | 5.83× | 3,480 | 23,526 | 6.76× | 164 |
| 8 | 4,092 | 46,140 | 11.28× | 11,184 | 156,444 | 13.99× | 648 |

The common-ground case also preserves exact state. Across its three workers, monolithic closure reports 417 candidate pairs and 1,308 Term evaluations; scoped sweeps report 2,289 candidate pairs and 8,067 Term evaluations.

The native operation-work trace records scheduler details for monolithic `run_rules_report`. Scoped sweeps currently emit only their operation-kind marker rows, while the scale-audit counters still record candidate and Term work. Therefore scheduler-row totals are not comparable between the two modes; use the separately captured scale counters for the search-work comparison. This instrumentation asymmetry is a concrete engine observability gap.

## Interpretation and next work

This is evidence that explicit task scopes can reproduce closure on these authored fixtures when every scope is exhaustively reswept to quiescence. It is also evidence that this conservative implementation has sharply higher search work as the number of goals grows. It does not establish learned frames, dependency completeness, factorization, speedup, or prevalence on natural tasks. It provides no justification for treating the proposed cheap-cut prior as an engine theorem.

Next, instrument scheduler work consistently inside scoped closure, then test activation-derived scopes without injected ownership annotations, with shared-state and cross-frame mutation controls. Keep candidate/Term work, scheduler rows, discovery cost, and closure cost separate. Expand to independently sourced task families before making locality or general capability claims.

Artifacts: [preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_3_PREREG_20261003.md), [runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_3.py), [analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_3.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_3_lock_20261003.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_3_20261003.json), and [independent analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_3_analysis_20261003.json). Failed/pre-analysis revisions are retained under explicit legacy filenames for audit and are not confirmatory evidence.
