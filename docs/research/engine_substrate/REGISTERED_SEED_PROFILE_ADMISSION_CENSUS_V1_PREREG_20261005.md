# Registered seed-root finite-key admission census v1 preregistration

## Question and scope

Does any root in the current `SeedRegistry` resolve to a bootable, nonempty executable-rule profile wholly admitted by the conservative finite-key insertion-only checker? The census extends the already completed 17-root core census to every registered root, including roots that fail due to missing manifests/dependencies. It is a coverage measurement, not a termination test or a prevalence estimate over natural workloads.

## Locked population and procedure

The population is the exact `REGISTRY.known()` order after importing `domains.seed_registry`, without filtering roots by apparent rule content. Record one row per registered ID. For each row, resolve its declared dependency closure. Preserve a `root_manifest_missing` or `dependency_manifest_missing` outcome explicitly; do not count it as accepted or remove it from the denominator. For bootable roots, construct a fresh `boot_core(seeds=(root,))`, export all active rules and the full initial node/edge inventory, apply the current `analyze_mint_termination_fragment.analyze` checker per rule and to the complete profile, and retain all decisions and reasons. The independent analyzer reimplements the syntactic acceptance predicate from the captured specs.

## Admission gates and outcomes

The source/native/manifest lock must remain stable; exactly one row must exist for every registered ID; all active rules, including duplicate rules across roots, must be analyzed; checker decisions must match the independent predicate; root and dependency failures must remain explicit; and a profile counts as a candidate only when it booted, has at least one active rule, and every active rule is accepted. Outcomes are the number of fully admitted nonempty profiles, individually admitted rules, empty profiles, and unavailable profiles, plus rejection reason counts. A zero result means the current checker does not cover any existing registered root profile. It does not imply rejected profiles diverge.

## Design status and claim boundary

An unrecorded exploratory sweep motivated this broader denominator. The locked rerun is a reproducibility audit of coverage on current source, not an independent blind sample. It does not demonstrate that an admitted profile is useful, that booting covers runtime rule mutation, or that termination is enforced. If no root is admitted, the next design must author a restricted profile or prove a broader sound class; do not reinterpret checker rejection as failure of the substrate.

## Reproduction

Create the lock with `python3 evaluation/substrate_capability/registered_seed_profile_admission_census_v1.py --lock`, capture with the same runner without arguments, then analyze with `python3 evaluation/substrate_capability/analyze_registered_seed_profile_admission_census_v1.py`.
