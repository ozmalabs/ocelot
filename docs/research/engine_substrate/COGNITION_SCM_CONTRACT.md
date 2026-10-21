# P5.E3 — Explicit finite structural causal models

**Status:** E3.1 contract, R1–R4 native evaluator and E3.2 default-off query caller are implemented. `ScmPolicy.enabled=0` by default. The seed caller writes detached results to `ScmQuery` records; there is no live-graph mutation or result promotion to observation/action.

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

SCM evaluation consumes a detached, epoch-tagged model snapshot and returns a result record containing query kind, treatment/outcome values, mechanism/source IDs, source epoch, assumptions, result or `unknown` reason. The E3.2 graph query record also retains the source model digest and epoch without promoting the detached result. Evaluation never edits live CAN state, `CausalFact` nodes, mechanisms, observations or goals, and does not authorize actions. `ScmPolicy.enabled` remains disabled outside explicit cognition-on evaluation.

The Rust Term obtains fixed result keys, statuses and abstention reasons from a reserved `Sym` vocabulary at the top of the symbol range. This keeps evaluation pure with the immutable `EvalCtx` interner and leaves ordinary per-substrate symbol allocation unchanged.

## Native term decision

Generic Terms can filter/map supplied finite rows, but do not provide one bounded operation that validates complete equation tables, topologically evaluates a model, enforces shared exogenous assignments and registered backdoor criteria, and returns an auditable abstention result. Python must not host those decisions. The pure `SCMIntervene` Term takes `(model, query, intervention, exogenous_assignments, assignment_cap)` and returns `status`, `values`, `assumptions`, `source_ids`, `source_epoch` and `reason`. `model` is a detached finite dict: `variables` and `exogenous` are lists of `{id, domain}`; `equations` is a list of `{target, parents, exogenous, rows}`, where each row is `{inputs: {parent_or_U_id: value}, value}` and rows cover the declared Cartesian product exactly once. `query` is `{kind: effect|condition|unit_counterfactual|adjustment, outcome: variable_id, adjustment?: [variable_id]}`. For `adjustment`, `intervention` must contain one treatment value and every positive-mass stratum in the supplied uniform exogenous population must have treatment support; each returned `values` row is `(stratum_tuple, standardized_sample_weight, outcome_value)`. A treatment descendant, open backdoor path, or unsupported stratum returns `unknown`. For `condition`, intervention values filter the observed/generated population without equation replacement. Unit counterfactuals preserve the same exogenous assignment. The evaluator has no graph handle and cannot mutate live state.

## Development acceptance fixtures

`test_do_differs_from_conditioning` uses a common cause U where conditioning on X predicts Y but `do(X)` leaves Y's marginal unchanged. `test_confounder_adjustment_matches_oracle` requires a valid U adjustment to recover the known zero effect from a confounded table. `test_collider_not_adjusted` verifies that conditioning on X→C←Y opens a path and rejects C. `test_no_identification_returns_unknown` covers a cycle and a positivity failure. `test_live_graph_unchanged` snapshots the input graph/model and checks byte-for-byte equality after detached evaluation. These fixtures define the contract; held-out SCM evaluation remains separate.
