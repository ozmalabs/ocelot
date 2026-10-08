# Native candidate-adequacy query gate v1.1 results

## Outcome

The corrected source-locked run completed all 80 workers in 40 paired panels. Capture gates passed, and the independent analyzer passed all 12 checks, including exact query-order replay, target-identity exclusion, native help after a mismatch, disjoint queried/transfer rows, and held-out prediction replay.

The baseline selected the supplied correct family in all 20 additive/product controls and requested help on all 10 inequality panels. On opposition, it requested help on 9/10 panels, leaving one false accept. In that one panel, candidate-positive querying found a product-positive row labeled false on query 1; the native graph changed the decision to `request_help`, and the four-query budget stopped after one label. Uniform selection used all four labels, found no mismatch, and left the wrong product candidate selected. Neither arm found a mismatch on any positive control; both used 40 total labels across the 20 control panels. Queried rows were excluded from final transfer scoring.

| Task | Baseline help / selection | Candidate-positive arm | Uniform arm |
|---|---:|---|---|
| Additive | 0 help; 10 selected correctly | 40 labels; 0 mismatches; no false help | 40 labels; 0 mismatches; no false help |
| Product | 0 help; 10 selected correctly | 40 labels; 0 mismatches; no false help | 40 labels; 0 mismatches; no false help |
| Opposition | 9 help; 1 wrong candidate selected | 1 label on the accepted panel; finds mismatch and requests help | 4 labels; misses mismatch; wrong candidate remains selected |
| Inequality | 10 help; no selection | Query skipped | Query skipped |

This demonstrates the intended handoff for one observed error: host-side target-blind ranking uses native predictions to choose a query, then native graph rules convert the revealed mismatch into help. The cohort had only one baseline false accept, so the difference between arms is not a stable detection-rate estimate. Query selection remains a host operation, and the task family and candidate menu are supplied.

## Provenance notes

The initial v1 capture is preserved with a failed query-receipt gate. V1.1 uses explicit false-positive and false-negative Boolean rules; its first worker capture passed, but the analyzer stopped on a paired-counter implementation error. That capture and lock are preserved as `pre_analyzer_fix` artifacts. A later audit caught a declared-but-vacuous prediction replay check; the passing intermediate capture, lock, and analysis are preserved as `pre_prediction_check_fix` artifacts. The final analyzed v1.1 run binds the corrected analyzer hash and reruns the same preregistered panel IDs. This is an implementation-corrected replay, not a second independent cohort.

## Reproduction and evidence

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_1.py --lock`, then `--run`, followed by `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_1.py`.

- [V1.1 amendment and correction log](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_1_AMENDMENT_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_1_lock_20261005.json)
- [Capture](../../../evaluation/reports/native_candidate_adequacy_query_v1_1_20261005.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_1.py)
- [Analysis](../../../evaluation/reports/native_candidate_adequacy_query_v1_1_analysis_20261005.json)

The result does not establish general adequacy repair, autonomous query selection, or self-improvement. It establishes a bounded native mismatch-to-help mechanism and motivates a larger fresh replication with enough out-of-menu false-accept panels to estimate query effectiveness.
