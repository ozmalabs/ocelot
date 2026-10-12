# Task-derived anaphora join-order replay v1 preregistration

Date: 2026-09-28 local

## Question

For a second task family with a linear four-edge match pattern, how much does native candidate work for the `rule_anaphoric_it_resolves_to_prior_about_concept` rule vary across authored clause orders, and does the task output remain invariant?

## Task and path

Use the exact two-turn positive case already present in `tests/test_intent_migrated.py`: first `the question matters`, then `answer it`, both as user statements. Initialize a `WorldAdapter` with no default seed set, then load the recursively declared dependency closure for `intent` through `load_seeds_into` (the current closure includes `intent`, `conversation`, `psychology`, `relations`, and `faculty_lessons`). This preserves the production utterance/comprehension adapter and the graph-authored native rule while excluding unrelated seed families. The independent task oracle is that the second message's `it` Mention resolves to the `question` Concept and its Intent carries the same `about_concept`.

Remove and reinstall only the target rule, permuting all four authored match clauses (24 permutations). Preserve its predicate/effects and other loaded rules. Read back the installed order after `add_rule`; do not assume it preserves the requested permutation. Run two fresh processes per permutation (48 workers), in a seeded shuffled schedule. On the second turn only, collect native global, per-rule, and per-clause matcher counters. Run a one-step terminal report after comprehension with audit disabled.

## Gates

- Exactly 48 unique fresh worker PIDs, all 24 permutations represented twice, and source/native inputs stable against a pre-run lock.
- The installed four-clause order is read back and is exactly a permutation of the four source clauses. Report requested-to-installed mapping and collapse repeated installed orders; do not assume the installer realizes all 24.
- Both turns complete; the second closure reaches a fixed point under the registered task budget.
- Every worker passes the independent anaphora oracle; compare canonical full graph digests across permutations and report any divergence.
- Target-rule per-clause candidate counts sum to the target-rule candidate-test total. Record predicate/Term work separately when the counters expose it.
- Report candidate work by installed order and replicate. Timing is secondary because counters are enabled; do not claim speed from this panel.

## Claim boundary

This is a selected synthetic utterance pair exercising the repository's existing anaphora test case, a minimal declared seed profile, one linear rule, 24 orders, and two process repeats. It is a second topology-specific matcher observation, not a natural conversation distribution, general join-order optimizer, complexity theorem, or substrate-wide tractability result. Preserve failures and partial runs. Do not modify the seed or production matcher as part of this study.
