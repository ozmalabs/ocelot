# Operator-shape selection transfer v1.1.1 — amendment

V1.1's capture is complete and its behavioral gates pass. Its copied analyzer still reconstructed the expected schedule from JSON object iteration order instead of the newly registered `task_order` and `wording_order` arrays, so the schedule-integrity gate remains false. V1.1 is preserved but not used as the confirmatory result.

V1.1.1 changes only the analyzer's schedule reconstruction to use those explicit locked order arrays and takes a fresh source/native lock and capture. Task examples, requests, schedule seed/order, runner behavior, source set, candidate budgets, scoring, and behavioral gates remain unchanged. This amendment closes the analysis defect without interpreting or pooling the earlier raw captures.
