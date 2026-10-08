# Native candidate-adequacy query v1.5 preregistration

## Question

Does the rebuilt matcher, including the repeated-variable incremental seed correction, preserve end-to-end v1.4 query behavior and cost on fresh task panels?

## Design

Repeat the four-task, three-arm query panel with 40 fresh paired panels, ten each for additive, product, opposition, and inequality, and 120 workers. Use fresh seeds beginning at 980000. Preserve balanced validation, minimum-class accuracy threshold 0.98, four-query budget, task-blind rank, candidate menu, and held-out task pool. The rebuilt native artifact and current source are locked before execution. Report stage and total cost separately and compare with v1.4 descriptively.

## Gates

Require all workers, current source lock, native/host candidate-positive query-order and decision parity, score and prediction replay, task identity exclusion, native mismatch-to-help behavior, query/validation/transfer disjointness, and held-out replay. This cohort is a regression gate; its false-accept count is not a prevalence estimate.

## Limits and reproduction

This remains a synthetic numeric task family with host-provided candidate menu, label oracle, and task-blind rank. It does not establish autonomous candidate generation or natural-task prevalence. Create the source/panel lock with `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_5.py --lock`, execute with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_5.py`.
