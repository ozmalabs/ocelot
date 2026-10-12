# Candidate-positive counterexample query utility: exploratory replay

## Purpose and limitation

This post-hoc analysis estimates whether a fresh, target-blind query policy could address the three v3 opposition false accepts. It reuses v3's sealed held-out rows, so it is exploratory evidence only. The query ranking was specified after v3 results were observed; a confirmatory result requires new panels and a preregistered query schedule.

## Policy replay

For each panel where v3 selected a candidate, rows are ranked by a deterministic SHA-256 key derived from the task/worker and row. The rank uses no target labels. Two pools are compared: all held-out rows, and only rows where the selected candidate predicts true. After selecting the first 1, 2, 4, or 8 rows, the analysis checks whether any selected row's target label differs from the candidate prediction. A mismatch is the counterexample that would trigger help.

Across the 23 selected panels, the candidate-positive pool has 8,719 rows and 972 candidate errors (11.15%). The uniform pool has 84,295 rows with the same 972 errors (1.15%). At budget one, candidate-positive queries find a counterexample in all three false-accepted opposition panels, while uniform queries find one of the three. At budgets two, four, and eight, candidate-positive finds all three; uniform still finds only one. Neither policy produces a false help on the 20 selected positive controls. These rates are conditional on only three opposition false accepts and a post-hoc deterministic ranking, so they do not estimate general query efficacy.

## Evidence and next gate

The replay input is [the v3 capture](../../../evaluation/reports/native_candidate_adequacy_v3_20261005.json) and [independent v3 analysis](../../../evaluation/reports/native_candidate_adequacy_v3_analysis_20261005.json). The deterministic analyzer is [here](../../../evaluation/substrate_capability/analyze_native_candidate_adequacy_probe_utility_v1.py); its output includes capture and analyzer hashes at [this report](../../../evaluation/reports/native_candidate_adequacy_probe_utility_v1_20261005.json).

A fresh confirmatory gate should keep the v3 adequacy decision, then spend a preregistered budget of four target-blind candidate-positive queries for accepted candidates. Each query must be disjoint from validation and final transfer, and a native rule should convert a revealed prediction mismatch into `request_help`. Compare candidate-positive selection with uniform selection at the same budget. Report label cost, help detection, false help on positive controls, query and decision latency, and held-out accuracy after queried rows are removed. The experiment should make clear that the current query ranking is a host policy over native predictions; native query selection would be a later responsibility-transition gate.
