# Native candidate-adequacy query gate v1.2 preregistration

## Question

Can query selection move from host code into native graph rules while preserving the target-blind candidate-positive policy, and does the native selector match its host control on fresh panels?

## Fresh panels and arms

Generate 10 new deterministic panels for each additive, product, opposition, and inequality relation, with seeds `940000 + task_index*100 + replicate`. Each panel has 16 positive and 16 negative validation rows using the v3 stratified seeded algorithm. Native graph rules score the supplied additive/product candidates by `min(TPR,TNR)` and select with threshold 0.98. The remaining integer and fractional rows form the fresh query/transfer pool.

Each panel has three paired arms with the same validation rows: (1) `candidate_positive`, where the host selects the first four rows on which the selected candidate predicts true; (2) `native_candidate_positive`, where native graph rules form that candidate-positive set and select each row using `ArgminUnique`; and (3) `uniform`, where the host selects the first four rows from all fresh rows. The host assigns each row a numeric priority from SHA-256 of replicate index and row, excluding task identity and labels. The native arm receives only these priorities and graph input facts; it derives eligibility from the selected candidate's native prediction and selects the lowest-ranked unqueried row. Host code marks a queried row unavailable after label acquisition.

Labels are revealed sequentially for up to four rows. A native rule changes the decision to `request_help` on the first selected-candidate prediction/label mismatch. Queried rows are removed from final transfer scoring. Final labels remain outside the graph. The query selection policy is fixed before the fresh seed cohort is evaluated.

## Gates

Require source lock/stability; 120 workers over 40 paired panels; exact validation balance and zero/boundary coverage; native baseline-score replay; no task identity in graph attributes or row ranking; exact native/host candidate-positive query-order parity; correct native mismatch-to-help decisions; query/validation/final-transfer disjointness; independent candidate prediction replay; and final held-out scoring after queried rows are removed. Report query closure costs separately from label count, help detection, false help, false acceptance, and transfer accuracy.

## Responsibility boundary and limits

The native arm moves prediction-based eligibility and ranked query selection into graph rules. The host still constructs and ranks the row descriptors, reveals oracle labels, and marks queried rows unavailable. This measures one bounded transfer of responsibility over a supplied two-candidate menu; it does not test open-ended hypothesis generation or natural-task query value.

## Reproduction

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_2.py --lock`, then `--run`, then `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_2.py`.
