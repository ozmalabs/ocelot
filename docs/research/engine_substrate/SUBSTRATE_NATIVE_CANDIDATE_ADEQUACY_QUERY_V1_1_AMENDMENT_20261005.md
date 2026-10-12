# Native candidate-adequacy query gate v1 preregistration

## Question

On fresh panels, does querying rows where the accepted candidate predicts true expose false accepts more efficiently than uniform queries, while native graph rules convert a revealed mismatch into a help request?

## Design

Generate ten new deterministic panels for each additive, product, opposition, and inequality relation, using seeds `930000 + task_index*100 + replicate`. Each panel has 16 positive and 16 negative validation examples selected by the balanced v3 algorithm from `(-3,-2,-1,0,1,2,3)^4`. Native graph rules rank the additive/product menu by `min(TPR,TNR)` and accept at 0.98. The complete integer complement plus 1,296 fractional rows forms the fresh query/transfer pool. V3 panel seeds and held-out captures are not reused.

Each panel runs two paired arms with the same validation rows: `candidate_positive` and `uniform`. The host harness orders rows by SHA-256 of replicate index and row only; task identity and labels are excluded from ranking. Candidate-positive arm filters to rows where the selected candidate predicts true; uniform arm uses every available row. Query budget is four, without replacement. Labels are revealed sequentially. A native graph rule changes the decision to `request_help` on the first selected-candidate prediction/label mismatch. Correct queries continue until budget is exhausted. If baseline already requests help or abstains, query is skipped.

Queried rows are excluded from final transfer scoring. The remaining rows stay unlabeled in the graph; after native decisions are captured, the harness independently scores them. Record actual labels used (early stop can reduce the budget), help detection, false help on positive controls, pre/post query selection, per-family held-out confusion, query-pool size, and native closure costs. Panel is the task unit; the paired arm comparison is within the panel.

## Gates and limits

Require source lock/stability, 80 workers over 40 paired panels, exact validation balance and coverage, target identity absent from graph state and query ordering, native score replay, exact target-blind query-order replay, query/test disjointness, correct native mismatch-to-help behavior, no held-out label leakage, and independent final transfer scoring. This tests a supplied two-candidate menu and a harness-selected query policy. Query selection remains host-side; only candidate prediction, adequacy, and mismatch-to-help decisions run in the substrate. It does not test open-ended hypothesis generation or natural-task query value.

## Reproduction

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_1.py --lock`, then `--run`, then `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_1.py`.


## V1.1 correction record

The initial v1 capture is preserved at `evaluation/reports/native_candidate_adequacy_query_v1_20261005.json`; its `query_receipts_valid` gate failed. Inspection showed the native `Not(Eq(prediction,label))` guard requested help on matching labels. V1.1 replaces that guard with two explicit Boolean mismatch rules: candidate true/label false and candidate false/label true. No panel generator, threshold, query ranking, budget, task, or scoring outcome was changed. V1.1 reruns the same preregistered panel IDs under a new source lock to isolate and correct this rule-encoding defect; it is an implementation correction, not an independent replication cohort.


The first corrected-rule capture passed all worker-level gates, but its analyzer stopped before producing an analysis because the paired-panel counter was initialized as an integer Counter. That capture and lock are preserved with `pre_analyzer_fix` in their filenames. V1.1 reruns under the corrected analyzer's source hash; this changes no query policy or scoring rule.


A subsequent audit found that the analyzer's `native_candidate_predictions` check was declared but not accumulated. The passing capture, lock, and analysis are preserved with `pre_prediction_check_fix` names. The final replay updates that check with explicit equality of every queried and remaining held-out candidate prediction against the independent formulas, and binds a new lock to the corrected analyzer.
