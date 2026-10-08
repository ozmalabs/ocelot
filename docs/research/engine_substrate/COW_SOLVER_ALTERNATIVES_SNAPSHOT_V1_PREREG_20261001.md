# Solver-alternative reusable snapshot consumer v1 preregistration

Date: 2026-10-01

## Question

Can an actual solver/planner consumer run multiple local alternatives from one immutable `SubstrateSnapshot`, with reusable CoW branches preserving solver results and primary/sibling isolation against eager-copy controls?

## Workload

Load the current native CAN rule seed into a fresh Substrate and construct one four-concept Microtheory with bidirectional weighted influences. For each of four preregistered perturbations to one concept's external field, create one branch from a shared `snapshot("shared_graph_pages")` and one eager deep-copy branch from the same primary revision. Invoke the production `domains.can_native_orchestration.scoped_settle` and `native_audit_basin` on each branch. Repeat each perturbation across five fresh worker processes, varying only deterministic initial field/weight values under the recorded seed schedule (20 worker processes total).

The primary model, candidate order, rule set, and perturbations are matched across backends. A solver alternative is a speculative branch; there is no implicit adoption. The source revision and baseline graph digest are retained in every worker.

## Gates

- Complete all 20 unique perturbation × replicate cells in fresh processes under stable source/native locks.
- The reusable snapshot reports the expected backend and source revision.
- Every child begins from the same pre-branch model; reusable and eager solver outputs match exactly on settled concept state, steps, energy, frustration, and graph facts.
- Each branch's changed input and solver mutations stay isolated from the primary, immutable snapshot, and sibling alternatives; all later forks begin from the baseline state.
- Report branch creation and solve costs descriptively; this is an integration/isolation test, not a speed threshold.

## Limits

This is one small native CAN solver, one four-concept topology, and four external-field perturbations. It does not validate solver optimality, general planning, concurrent mutation, cancellation/reclamation, adoption/conflict policy, natural-task prevalence, large-scale speed, or vLLM-style serving.
