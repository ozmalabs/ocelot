# Native candidate-adequacy query gate v1.2 results

## Outcome

The source-locked fresh run completed all 120 workers in 40 three-arm panels. Capture checks passed, and the independent analyzer passed all 14 checks, including exact native/host query-order parity, target-identity exclusion, native mismatch-to-help behavior, query/transfer disjointness, and prediction replay.

On the 20 additive/product controls, all arms selected the correct candidate and found no queried mismatches. Each arm spent 80 labels across these controls with no false help. On opposition, the baseline selected the wrong product candidate in three of ten panels and requested help in seven. Both host and native candidate-positive arms found counterexamples in all three false-accept panels using four labels total; native rules requested help in each case. The uniform arm used 12 labels across those three panels, found one counterexample, and left two wrong candidates selected. Inequality panels all requested help at baseline, so query selection was skipped.

The native selector matched the host candidate-positive selector in every paired panel: same queried rows and final decisions. This is a verified responsibility transfer for candidate-prediction filtering and ranked row selection. The host still generates a target-blind rank for every row and reveals oracle labels; graph rules handle eligibility, `ArgminUnique`, adequacy, and mismatch-to-help.

## Cost

Native selection is substantially slower in this implementation. Among the 23 panels per arm that selected a candidate, median worker CPU time was 1,292 ms for the native selector, versus 299 ms for the host candidate-positive selector and 296 ms for uniform. Native query eligibility closure had an 84 ms median, and the repeated native selection closures had a 920 ms median total per selected worker. The measured implementation repeats graph selection for each query across the full row population. The next engine gate should reduce this cost, for example by introducing an incremental candidate index or a batched top-k primitive, then rerun the same paired correctness checks.

## Interpretation limits

Only three opposition panels passed the baseline gate, so query effectiveness has a small challenge denominator. The result supports exact selector parity and one bounded native mismatch-help route; it does not estimate natural-task query benefits. Query order priority and labels remain harness supplied, the candidate menu is fixed, and no new relation is invented.

## Reproduction and evidence

Run `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_2.py --lock`, then `--run`, followed by `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_2.py`.

- [Preregistration](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_2_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_2_lock_20261005.json)
- [Capture](../../../evaluation/reports/native_candidate_adequacy_query_v1_2_20261005.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_2.py)
- [Analysis](../../../evaluation/reports/native_candidate_adequacy_query_v1_2_analysis_20261005.json)
