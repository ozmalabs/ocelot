# Task-derived anaphora join-order replay v1 results

Date: 2026-09-28 local

## Outcome

The locked run completed 48 fresh workers covering all 24 authored permutations of the anaphora rule's four match clauses, with two workers per permutation. The independent analyzer passes **293/293 checks**. All workers retain the exact task output: the second message's `it` Mention resolves to `question`, and the Intent contains `question` among its `about_concept` values. Every terminal probe reports `fixed_point`; canonical full-graph digests match across all 48 workers. Per-clause target-rule candidate counts sum exactly to each worker's per-rule candidate-test total.

The native installer realizes **8 distinct orders** from the 24 requested permutations. Candidate tests for the target rule range from **8 to 16**, with exact counts repeated across the two fresh processes for each requested permutation. The source-authored order (`has_mention → responds_to → has_intent → about_concept`) is realized by 12 requests and costs **13 candidate tests**. The lowest-work installed order costs 8 tests (1.63× below the source order); the highest costs 16 (1.23× above). Thus this second task family shows lower order sensitivity than the cyclic common-ground rule's 3.86× spread, and its optimum does not imply a useful global order policy.

The audit-on closure timer ranges from about **0.123 to 0.151 ms** by installed-order median. These timings include per-rule/per-clause instrumentation and are secondary diagnostics, not uninstrumented speed evidence. The recorded task inputs, recursive five-seed dependency closure, test source, runtime adapter, matcher/audit sources, analyzer, protocol, native extension, and build manifest remained stable. The common `substrate-run-manifest-v1` records hardware/toolchain, explicit input hashes, parent log hash, and 48 child-log hashes; independent log checks confirm all 48 logs exist and match their recorded hashes. The native build was current at capture.

## Interpretation and limits

This is a second task-shaped pattern family and a directly measured native matcher path. It shows that reordering can change candidate work while preserving both task output and exact graph state, but the tested graph is very small and nearly all permutations collapse into eight installed orders. It does not estimate natural conversation frequency, uninstrumented latency gains, estimator accuracy, or cost at larger graph sizes. The input is one authored test example, not an externally sampled task distribution.

The initial pilot showed that the Intent also contains `answer` in `about_concept`. The [v1.1 amendment](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_1_AMENDMENT_20260928.md) records why the oracle follows the existing test's membership condition for `question` rather than requiring an exact singleton list. The pilot is preserved separately and is excluded from the 48-worker analysis.

## Evidence

- [Preregistration](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_PREREG_20260928.md)
- [Oracle amendment](SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_1_AMENDMENT_20260928.md)
- [Runner](../../../scripts/substrate_task_derived_anaphora_join_order_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_task_derived_anaphora_join_order_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/task_derived_anaphora_join_order_v1_lock_20260928.json)
- [48-worker raw capture](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_workers_raw_20260928.json)
- [Independent analysis](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_analysis_20260928.json)
- [Run manifest and log hashes](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_20260928.json)
- [Single-worker exploratory pilot](../../../evaluation/reports/substrate_task_derived_anaphora_join_order_v1_pilot_20260928.json)

Claim boundary: one linear four-edge anaphora rule, one two-turn example, a minimal declared seed profile, 24 authored orders, two process repeats, and native opt-in counters. No general join optimizer, natural prevalence, or CPU speed claim follows.
