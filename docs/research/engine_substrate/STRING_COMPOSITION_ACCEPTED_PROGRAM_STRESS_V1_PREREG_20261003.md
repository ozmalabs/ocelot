# Accepted string-program stress generalization v1 preregistration

Date: 2026-10-03

## Question

How often do programs accepted by the four frozen P4 arms compute their registered task function on a larger, independently generated input sample?

## Frozen protocol

For each of the 18 task specifications in the fresh string-composition suite, generate 50 unique inputs with the existing task-family sampler `make_rows`, using a new deterministic seed `20261003 + task_ordinal * 7919 + 1000003`. This creates 900 new inputs (50 per task), disjoint from the frozen seven rows. Use the same frozen task parameters and oracle definitions. For each accepted artifact in `main`, `no_retrieval`, `no_retrieval_escalated`, and `main_replay`, evaluate its saved IR on all 50 new rows for that task using native ProgEval. Gapped cases have no candidate and are reported as unavailable, not failures. A row is correct only if execution halts without a trap and output agrees with the frozen oracle under the benchmark's `agree` relation.

Report the number and fraction of correct rows for each accepted task-arm program, exact-on-50 program count, errors/traps, and aggregate accepted-program row accuracy. This is a diagnostic stress sample; it does not replace the original three heldouts, and the 50 rows are not independent task functions. No search, prompt, or acceptance decisions are rerun or changed.

## Claim boundary

This estimates generalization of the specific accepted programs on these generated input distributions. It does not estimate performance on natural tasks, prove semantic correctness for all strings, or attribute why the P4 verifier accepted a false program.
