# P5.E3 — Explicit finite structural causal models

**Status:** E3.1 contract and development fixtures. `ScmPolicy.enabled=0` by default. No SCM runtime, causal-effect claim, or live-graph mutation is implemented by this specification.

## Model and bounds

An SCM contains a finite set of endogenous variables `V`, each with an explicit nonempty finite domain, a finite set of exogenous variables `U` with explicit domains, and exactly one structural equation `f_i(PA_i, U_i) → V_i` for every endogenous variable. The endogenous dependency graph must be acyclic. Every equation must be total over the declared parent/exogenous product and return a value in its target domain. Missing, ambiguous, cyclic, or out-of-domain mechanisms are invalid and yield `unknown`; an association-only `CausalFact` is never promoted to an equation.

The first runtime cap is 16 endogenous variables, domain size at most 8 per variable, and at most 4096 joint exogenous assignments. Inputs over a cap return `unknown` with a bound reason. Exact finite enumeration is required; unsupported probability weights, continuous variables, hidden-equation learning and cyclic SCMs abstain. A `CausalFact` may reference a mechanism only with explicit `mechanism_id`, ordered parent IDs, target ID, equation table and source/model epoch. CAN concepts, `causal_influence` couplings, energy functions and correlation patterns remain associative unless an independent registered mechanism supplies this complete mapping.

## Intervention, conditioning and counterfactuals

`do(X=x)` replaces X's structural equation with the constant x for the query; all other equations remain intact and are evaluated in topological order. This is edge surgery on the detached model: incoming causes of X are removed for the intervention. Observational conditioning `P(Y | X=x)` filters the observed/generated joint population and does not remove X's causes. The two answers can differ under confounding, and the API returns them as distinct query kinds.

A unit-level counterfactual reuses the exact same exogenous assignment for factual and alternate worlds. It first evaluates the factual equations, then replaces the intervened equation while preserving all U values. Marginalizing with independently resampled U is not a unit-level counterfactual. Population effects integrate over the declared exogenous distribution; absent weights, the contract uses uniform mass over the explicitly enumerated joint assignments and records that assumption.

## Identification from observations

Observed backdoor adjustment accepts a set Z only if: (1) Z contains no descendant of X; (2) Z blocks every backdoor path from X to Y in the graph with outgoing edges from X removed; and (3) positivity holds, `P(X=x | Z=z)>0` for every included stratum with positive mass. The effect is standardized over the observed marginal distribution of Z. The solver reports the selected Z, stratum weights, conditional outcome rates, support counts and source epoch. An invalid set, zero-support stratum or missing required mechanism returns `unknown` instead of silently dropping the stratum.

Colliders and their descendants are not admissible merely because adjustment changes the numeric answer. A collider opened by conditioning fails the d-separation check in the mutilated graph. General do-calculus completeness is explicitly out of scope: if no registered valid adjustment set or finite SCM identifies the requested effect, return `unknown` with the unmet criterion. Do not choose a convenient set after observing outcomes.

## Isolation and provenance

SCM evaluation consumes a detached, epoch-tagged model snapshot and returns a result record containing query kind, treatment/outcome, intervention value, mechanism/source IDs, source epoch, assumptions, result or `unknown` reason, and model digest. It never edits live CAN state, `CausalFact` nodes, mechanisms, observations or goals. Results do not become world facts or action authorization without a separate evidence promotion path. `ScmPolicy.enabled` remains disabled outside explicit cognition-on evaluation.

## Native term decision

Generic Terms can filter/map supplied finite rows, but do not currently provide one bounded operation that validates complete equation tables, topologically evaluates the intervened model, enforces shared exogenous assignments, and returns an auditable abstention result. Python must not host those decisions. The spec therefore requires one pure `SCMIntervene` evaluator Term. Frozen shape: arguments are `(model, query, intervention, exogenous_assignments, assignment_cap)`; result is a record with `status` (`identified`, `unknown`, or `invalid`), `values`, `assumptions`, and `reason`. `model` is a detached finite data value with variables, domains, equations and source identities; `query` declares `effect`, `condition`, or `unit_counterfactual`; `intervention` maps variable IDs to in-domain values; `exogenous_assignments` is the finite assignment list used for evaluation. The evaluator has no graph handle and cannot mutate live state. R1–R4 are required; no seed caller is activated until R4 passes.

## Development acceptance fixtures

`test_do_differs_from_conditioning` uses a common cause U where conditioning on X predicts Y but `do(X)` leaves Y's marginal unchanged. `test_confounder_adjustment_matches_oracle` requires a valid U adjustment to recover the known zero effect from a confounded table. `test_collider_not_adjusted` verifies that conditioning on X→C←Y opens a path and rejects C. `test_no_identification_returns_unknown` covers a cycle and a positivity failure. `test_live_graph_unchanged` snapshots the input graph/model and checks byte-for-byte equality after detached evaluation. These fixtures define the contract; held-out SCM evaluation remains separate.
