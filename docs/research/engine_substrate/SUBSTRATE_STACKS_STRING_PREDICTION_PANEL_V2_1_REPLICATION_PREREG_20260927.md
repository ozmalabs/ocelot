# Stacks string-predicate panel v2.1 current-source replication preregistration

Date: 2026-09-27  
Status: frozen replication of the v2 candidate on the current full-runtime snapshot.

## Question and fixed protocol

Does v2's constrained lowering reproduce its exact behavior on the same 25 Stacks calls, five Unicode-prefix probes and two arithmetic controls when the runtime is locked to the current worktree? The only runtime-source difference observed between the v2 snapshot and this pre-run snapshot is `substrate/boot_profiles.py`, now hash `3dafdba4c1bece04c03e96cef3e0023c48a5eebafb80369c62463ec2b60ee166` vs v2's captured `7b8ce5aefe8b45e7207467945a39e8db83a2e9f8b1115866c40b8fe9aa93df84`. No evaluator, predictor, substrate domain, seed, native source, or workload changes are intended. The input frame and selector are identical to v2; the two controls remain last.

V2 raw, analysis and frame are frozen references with hashes `abe5421e4c67a25372ba67b3330a4af8b8a2119d0416b9e55df6305e0ebba1d9`, `f374eeaa12b8050ab4eb041ab0b845741badc5335182a530b1b5d42d4f13e93e`, and `5a0f2b31d30835ab44e664dc61a238ee5d76b32b5370b0750e66f394edbb8927` respectively. The runner/analyzer locks these files and verifies their hashes before scoring.

## Gates

Use two fresh workers with exact 27-call schedules; stable before/after full source locks; shared run manifest and hashed console log; independent frame/oracle reconstruction; all 25 Stacks outputs exactly match the oracle; both controls pass 2/2; no wrong values; worker prediction/error parity; and exact per-case prediction/error/mint parity against the frozen v2 raw capture. Report all cost and boot measures separately. This replication can establish current-snapshot repeatability for the targeted engineering path only. It does not remedy v2's design-after-inspection limitation or establish a new family transfer estimate.
