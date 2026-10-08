# Native query-selector scaling gate v1.3 preregistration

## Question

Can the native candidate-positive query selector retain v1.2 behavior while avoiding repeated full-pool rule matching?

## Optimization and comparison

Generate 10 fresh panels per additive, product, opposition, and inequality task with seed IDs 950000 + task_index*100 + replicate. Preserve the same 16/16 balanced validation construction, min(TPR,TNR) >= 0.98 baseline, four-label budget, task-blind rank derivation, final test pool, and three arms from v1.2: host candidate-positive, native candidate-positive, and host uniform.

The v1.2 native selection rule matched one graph edge for every probe row and evaluated the same ArgminUnique expression in each match. V1.3 anchors the rule on the unique selected_family edge, evaluates ArgminUnique once per query, and stores its selected node in the episode. Native eligibility remains derived from graph predictions; host code still supplies row priorities, labels, and queried-state updates.

## Gates

Require 120 source-locked workers, exact paired native/host query-order and final-decision parity, baseline score replay, task-identity exclusion, correct native mismatch-to-help, query/validation/final-transfer disjointness, and independent prediction/transfer replay. Report total worker cost, native eligibility and per-query selection closure time, and query adjudication time. The performance comparison is against the source-locked v1.2 capture, with fresh seeds and the same workload design.

## Interpretation boundary and reproduction

This is a bounded query-selector optimization, not evidence of general query competence. Query ranking remains harness generated; candidate menu and numeric tasks remain fixed.

Run python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_3.py --lock, then --run, followed by python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_3.py.
