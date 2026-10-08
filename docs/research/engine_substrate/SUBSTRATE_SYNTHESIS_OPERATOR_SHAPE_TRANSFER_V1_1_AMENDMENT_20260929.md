# Operator-shape selection transfer v1.1 — amendment

V1's capture completed all 20 workers and its behavioral analysis gates all pass. Its analyzer reports the schedule-integrity gate as false because the runner constructed the schedule using Python declaration order, while JSON lock serialization sorts object keys; the analyzer then reconstructed the schedule from the sorted lock maps. The capture contains the complete unique 20-cell matrix, but the analyzer did not prove exact schedule order. V1 is preserved and not used as the confirmatory result.

V1.1 records `task_order` and `wording_order` as explicit ordered lists in the lock and makes both runner and analyzer use those lists. Task definitions, wording strings, cases, schedule seed, arm order, source/native requirements, behavioral thresholds, and all other protocol conditions remain unchanged. V1.1 takes a fresh lock and repeats the 20-worker panel.
