# Bounded planner native unit audit preregistration

## Question

Do the five source-located Rust unit tests cited by the capability map pass against the current checkout and native toolchain?

## Fixed cases and commands

Run each exact test name separately from `runners/dsl` with `cargo test --lib <fully-qualified-test-name> -- --exact`:

1. `p2_bounded::tests::preserves_equal_minima_as_tie`
2. `p2_bounded::tests::fails_closed_for_incomplete_prediction_set`
3. `p2_bounded::tests::maximum_intervention_removes_over_budget_candidates`
4. `p2_native::tests::mechanics_control_real_transition_and_not_submitted_witnesses`
5. `p2_native::tests::maximum_intervention_excludes_over_budget_actions_in_worker_and_evaluator`

## Gates

All five commands exit zero and report exactly one passing test each. Record failure output verbatim if a command fails; do not rerun under changed code in this capture. The runner records command argv, stdout/stderr files and hashes, source/build inputs, toolchain, hardware, environment, and dirty-workspace fingerprint through the shared run-manifest utility.

## Claim boundary

Passing tests establish only the assertions in these five fixtures for this checkout. They do not establish long-horizon search, replanning, held-out-world performance, route activation, comparison with another planner, or general action-selection capability. No test source or implementation is changed by this measurement.
