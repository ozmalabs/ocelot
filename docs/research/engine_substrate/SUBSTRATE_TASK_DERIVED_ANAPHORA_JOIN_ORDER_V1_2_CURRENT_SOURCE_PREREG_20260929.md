# Anaphora join-order v1.2 current-source replay preregistration (2026-09-29)

## Question

Does the four-edge anaphora task's clause-order sensitivity reproduce on the current adapter, matcher, graph, audit, and native-extension sources?

## Design

Repeat the prior two-turn authored anaphora task for all 24 permutations of the four positive match clauses, with two fresh-process replicates per permutation (48 workers). Build only the registered `intent` seed profile, rewrite the one target rule's match array, feed the same two utterances, and capture task output, terminal fixed-point report, graph digest, per-rule and per-clause candidate counters. The independent analyzer checks task semantics, graph identity across all orders, per-clause candidate conservation, source stability, and child-log hashes.

## Source drift and integrity

The 2026-09-28 v1.1 lock no longer matches current `world_adapter.py`, matcher/graph/audit source, native extension, or build manifest. V1.2 uses new source/native hashes, a new runner/analyzer, distinct report paths, and fresh run logs. Preserve prior captures. Require current native build freshness, exact 48-cell coverage, 48 unique child processes, stable source lock at each worker and after the run, all logs present/hash-valid, task oracle and fixed-point success, all 24 requested clause orders realized as complete clause multisets, and identical graph digest across orders.

## Claim boundary

This is one small two-turn task and one four-edge rule on current sources. The native audit is enabled during the measured closure, so its timing is diagnostic only. Candidate tests show order sensitivity but not ordinary CPU speedup, natural-task prevalence, or a general optimizer.

## Reproduction

```sh
python3 scripts/substrate_task_derived_anaphora_join_order_v1_2.py --lock
python3 scripts/substrate_task_derived_anaphora_join_order_v1_2.py
python3 scripts/analyze_substrate_task_derived_anaphora_join_order_v1_2.py
```
