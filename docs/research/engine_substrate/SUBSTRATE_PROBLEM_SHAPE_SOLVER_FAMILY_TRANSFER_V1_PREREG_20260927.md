# ProblemShape solver-family transfer v1 preregistration (2026-09-27)

## Question

Can the graph-resident ProblemShape learner acquire and reuse the structural form of a real `solve_reasoning_bridge` Goal after recurrence, while preserving solver resolution and rejecting an opposite-direction near-neighbor? This extends v1's CAN relax/BP schema probe to a distinct solver interface and checks a seeded CAN exact control in the same workers.

## Design

Run two fresh full-seed workers on one locked runtime snapshot. Each worker:

1. Creates and settles three real CAN Microtheories from distinct locked Bigville resident records using `solve_can_exact`.
2. Observes one resolved exact-CAN Goal with `ProblemShape` as a seeded-codebook positive control; it must be recognized as `ps_has_targets_mt=yes` with no mint.
3. Mints, resolves, and observes three `solve_reasoning_bridge` Goals in the `can_to_deduction` direction, each targeting a different settled Microtheory. The first two are recurrence/training; the third is the positive held-out transfer. Expect the first to begin residual, the second to cause one mint and re-decode the first, and the third to be recognized by the same direction-plus-target-edge shape.
4. Mints, resolves, and observes one `deduction_to_can` Goal using the first resident's real entity name and `trust_mayor` field. This is a valid opposite-direction near-neighbor and must remain a singleton residual without a second mint.

The primary outcome is the observation rung and covered ProblemShape, separate from each underlying solver Goal's resolved/walled status and answer payload. Record each Goal's target, route, status, answer, signature key, initial/final observation status, mint delta, per-rule candidate/Term work, wall/CPU, seed boot counts/failures, peak RSS, and source/runtime lock. The public sequence and resident IDs are fixed before execution.

## Provenance and integrity gates

Use an immutable, read-only copy of the measured source/runtime snapshot. Hash all Python under `domains/`, `substrate/`, `runners/dsl/python/`, `worlds/`, and `scripts/`; all Rust source; all seed JSON; all files under `data/slabs/`; native extension/build metadata/Cargo manifests; protocol, runner, analyzer, and shared measurement helper. Capture one full lock immediately before and after the worker batch. Workers use that registered immutable lock; no source or seed asset is writable during execution.

Required gates:

- exactly two distinct fresh worker processes;
- full seed boot produces a nonempty loaded profile; record and reconcile the known manifest failures rather than silently excluding them;
- all eight underlying CAN exact/bridge Goals per worker resolve through their expected registered resolvers;
- seeded exact observation is recognized as `ps_has_targets_mt=yes` without mint;
- bridge observation 1 is residual before recurrence; observation 2 mints exactly one `ps_has_direction=can_to_deduction_has_targets_mt=yes` shape and re-decodes observation 1; observation 3 uses that same shape;
- opposite-direction Goal resolves but its observation remains residual and causes no additional shape mint;
- pre/post snapshot lock and source/analyzer hashes reconcile, with same outcome pattern across both workers.

## Limits

This is one real solver-family transfer probe with two workers. It tests recurrence and graph-structural reuse across distinct resident networks, not accuracy of the bridge's CAN interpretation, natural residual frequency, general schema induction, or transfer across domains. Candidate/Term counters are instrumented work, and cold full-seed boot is reported separately from per-observation cost. A task-contract failure is a result, not an exclusion.
