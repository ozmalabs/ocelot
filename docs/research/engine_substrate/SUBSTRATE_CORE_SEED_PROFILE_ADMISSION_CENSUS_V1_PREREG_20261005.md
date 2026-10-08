# Core seed-root finite-key admission census v1 preregistration

**Question.** Does any individual `CORE_SEEDS` root, loaded with its declared dependency closure, form a nonempty active rule profile wholly inside the existing finite-key insertion-only fragment?

**Method.** Under one source/native lock, boot each of the 17 default core seed roots independently via `boot_core(seeds=(seed_id,))`; do not run rules. Export the full active rule store and initial graph for each resolved profile. Apply the existing finite-key checker to the individual active rules and full profile. Record zero-rule profiles separately, since empty acceptance is vacuous.

**Independent analysis.** A separate analyzer re-implements the finite-key grammar gate, verifies exact root coverage, unique active rule identities, complete graph inputs, source-lock stability, checker/analyzer agreement, and aggregate profile decisions. Report per-root active-rule counts, accepted-rule counts, whether the full nonempty profile passes, and common rejection classes.

**Limits.** A passing root would identify a candidate restricted profile only; it would not show that it is sufficient for general cognition, that production routes enforce its restriction, or that the proof extends beyond the checker assumptions. Rejection does not imply nontermination. The survey does not change rule admission or execute any rule.
