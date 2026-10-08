# Native candidate-adequacy query v1.4 preregistration

## Question

Does the fully bound edge-membership fast path improve the end-to-end cost of the v1.3 native query responsibility panel while preserving exact native/host candidate-positive query order and decisions?

## Design

Repeat the v1.3 experiment on 40 fresh paired panels: ten each for additive, product, opposition, and inequality tasks, with host candidate-positive, native candidate-positive, and host uniform arms. Use fresh seed IDs beginning at 970000. Preserve the 16/16 balanced validation construction, minimum-class-accuracy threshold 0.98, four-label budget, task-blind hashed rank derivation, final test pool, candidate menu, and task identity exclusions. Run all 120 workers on the rebuilt current-source engine. Report total worker CPU/wall/RSS, native eligibility closure, per-query selection closure, query adjudication, and task-level outcomes. Compare selector and total native costs descriptively with v1.3; builds/captures are not same-session counterbalanced.

## Gates

Require 120 successful source-locked workers, exact native/host candidate-positive query-order and final-decision parity, baseline score and native prediction replay, task-identity exclusion, correct mismatch-to-help behavior, query/validation/transfer disjointness, and independent held-out prediction/score replay. Report whether the three previously observed opposition false accepts recur; do not use this small count to estimate prevalence.

## Limits

This is a replication of a bounded synthetic query workload after one matcher optimization. Candidate menu and query rank remain supplied by the harness. It does not test autonomous hypothesis generation, natural-task prevalence, general matcher correctness, or self-improvement.

## Reproduction

Create the immutable source/panel lock with `python3 evaluation/substrate_capability/native_candidate_adequacy_query_v1_4.py --lock`, run with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_4.py`.

