# Registered seed-root finite-key admission census v1.2 results

## Result

The source/native-locked census covers every 117 ID returned by the current `SeedRegistry`. Of these, 112 roots booted, including 82 nonempty executable-rule profiles and 30 empty profiles. One registered root (`curiosity_agent`) has no root manifest. Four others (`aperture_belief_gate`, `aperture_frame`, `fallback_vocabulary`, and `observer_aperture`) declare a dependency on missing `core.json`. Those five unavailable roots remain explicit and are not counted as candidates.

Across the 82 nonempty profiles, the checker examined 1,803 active rule instances. No rule passed individually, and no nonempty profile passed as a whole. The independent acceptance predicate agrees with every per-rule and aggregate decision; all seven integrity checks pass. The captured rules contain 6,615 effect occurrences: 3,894 `set_attr`, 1,456 `add_edge`, 634 unconditional `add_node`, 465 `set_attr_if_different`, 68 `del_node`, 59 `del_edge`, 28 `add_node_if_absent`, eight `net_collapse`, two `set_rule_clause`, and one `apply_rule_patch`. Rule fields beyond the checker schema are also common: 1,798 rows contain `where`, 437 `match_type`, and 142 `batch`; counts overlap.

## Interpretation

The current checker is not a usable admission gate for any existing registered seed root, and its fragment cannot be enabled on an existing root simply by selecting a passing subset of current rules: the per-rule pass count is zero. This is a source/profile compatibility finding, not evidence that those rules fail to terminate. A termination-bounded operating mode would need an explicitly authored restricted profile with useful behavior, plus enforcement covering every way rules enter or change the live substrate. The census alone does not demonstrate the utility or capability loss of such a profile.

The census was motivated by an unrecorded exploratory sweep; v1 and v1.1 preserve analyzer integrity failures. V1.2 is the complete admitted result and is a reproducibility audit on the current source tree, not an independent or blind task sample.

## Reproduction

The [protocol](REGISTERED_SEED_PROFILE_ADMISSION_CENSUS_V1_PREREG_20261005.md) fixes the population and missing-root treatment. [V1.1](REGISTERED_SEED_PROFILE_ADMISSION_CENSUS_V1_1_AMENDMENT_20261005.md) and [v1.2](REGISTERED_SEED_PROFILE_ADMISSION_CENSUS_V1_2_AMENDMENT_20261005.md) document analyzer corrections. Reproduce with the [v1.2 runner](../../../evaluation/substrate_capability/registered_seed_profile_admission_census_v1_2.py) and [independent analyzer](../../../evaluation/substrate_capability/analyze_registered_seed_profile_admission_census_v1_2.py). The [lock](../../../evaluation/substrate_capability/registered_seed_profile_admission_census_v1_2_lock_20261005.json), [capture](../../../evaluation/reports/registered_seed_profile_admission_census_v1_2_20261005.json), and [analysis](../../../evaluation/reports/registered_seed_profile_admission_census_v1_2_analysis_20261005.json) preserve the full evidence.
