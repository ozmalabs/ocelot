# Clause-aware generated guards v1 results (2026-10-04)

## Findings

The locked six-panel evaluation passes all seven independent analysis gates.
The direct-comparison generator emits one useful row for each interval
arity-2/3/4 panel and the nested interval-disjunction panel. It resolves the
false candidate in one oracle label in each case. Pairwise proposals alone
already resolve the arity-2 and nested panels, but falsely accept the
arity-3 and arity-4 interval candidates without labels.

The `Plus` and `Times` equality guards are outside the proposal generator's
supported syntax. Pairwise finite-class logic accepts both false candidates
with zero labels. Clause-aware completeness tracking detects the unsupported
branch and returns `request_help` in both cases, with zero labels and no false
acceptance. This tests the intended fail-closed path.

| Panel | Clause rows | Unsupported branches | Clause labels | Clause decision | Clause native evaluations | Pairwise outcome |
|---|---:|---:|---:|---|---:|---|
| Interval, arity 2 | 1 | 0 | 1 | Accept identity survivor | 192 | Resolves in 1 label |
| Interval, arity 3 | 1 | 0 | 1 | Accept identity survivor | 240 | False candidate accepted |
| Interval, arity 4 | 1 | 0 | 1 | Accept identity survivor | 450 | False candidate accepted |
| Nested interval disjunction | 1 | 0 | 1 | Accept identity survivor | 450 | Resolves in 1 label |
| Unsupported `Plus` equality | 0 | 1 | 0 | Request help | 212 | False candidate accepted |
| Unsupported `Times` equality | 0 | 1 | 0 | Request help | 212 | False candidate accepted |

## Interpretation and limits

The result shows transfer across selected direct-comparison forms and correct
abstention on two unsupported arithmetic forms. The extractor and fail-closed
policy are harness-authored. The substrate supplies native Term evaluation
and query selection; it did not acquire this method. Only six guards were
tested. Unsupported-branch detection here does not certify that every
supported branch's satisfying assignments are complete, and the finite
behavior acceptance remains unproved outside its queries. Next expand the
generated grammar across mixed arithmetic, nested boolean structure,
contradictory conjunctions, and variable aliasing; distinguish proven-unsat
branches from solver failure; and keep help as the outcome whenever semantic
coverage is unresolved. This is not a general clause-solving or tractability
result.

## Reproduction

- [Protocol](CLAUSE_AWARE_GENERATED_GUARDS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/clause_aware_generated_guards_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_clause_aware_generated_guards_v1.py)
- [Lock](../../../evaluation/substrate_capability/clause_aware_generated_guards_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/clause_aware_generated_guards_v1_20261004.json)
- [Analysis](../../../evaluation/reports/clause_aware_generated_guards_v1_analysis_20261004.json)
