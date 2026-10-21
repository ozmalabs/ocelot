# Cognition planner contract v1

## Purpose and authority

The planner supplies bounded, model-based **candidate plans** to System 2. It does not issue actions, change world state, certify a transition as true, or satisfy a goal by itself. Each result is an `ImaginedPlan` with `provenance_kind="imagined"`, `observation_status="not_observed"`, and `grounding_status="ungrounded"`. An execution candidate is reopened only by E4.3's explicit arbitration contract and must pass the current goal, manifold, action-inhibition, and sink-authorization checks again.

`generative_world_model` owns admissible action-conditioned successor proposals and their uncertainty. The planner may only expand successor records linked to the exact source state and current model version. Missing or stale transitions never imply a wait action. A branch remains uncertain when the model gives an uncertainty envelope; the planner preserves the branch and cannot collapse it into a fact.

## Identity and snapshot

A planning request freezes `(request_id, owner_id, source_epoch, model_id, model_epoch, goal_id, goal_epoch, manifold_id, manifold_epoch, start_state_id, depth_limit, expansion_limit)`. The default limits are depth 8 and 256 unique expanded states. The effective limits are the minimum of request and enabled policy limits. The immutable request snapshot is the provenance root for all frontier states and returned plans.

A state key is `(model_id, model_epoch, state_id, goal_id, goal_epoch, manifold_id, manifold_epoch)`. Reaching a key already expanded or present in the current ancestor chain does not enqueue another expansion. This terminates cycles while keeping distinct states, goals, model revisions, and manifold revisions separate. State identity is graph identity supplied by the model; no Python hash or approximate state merge decides equivalence.

## Expansion and budget

The frontier is graph-resident. Each frontier item records its state key, parent item, incoming transition, depth, path identity, source model version, uncertainty envelope, and status. The selector takes the lowest stable frontier rank, with rank assigned by graph rules at insertion; ties use node identity. One expansion requires one current-epoch `ThinkingBudgetRequest` debit before reading/expanding successors. The debit is single-use and keyed by request ID, state key, and model epoch. No debit means no expansion. Denial, exhaustion, deadline, or epoch mismatch closes the planning request with an explicit status and does not partially expand a state.

The planner increments `expanded_count` exactly once per unique state key, and never above 256. It never generates successor records itself. At depth 8, it may recognize a goal state but cannot expand it further. Budget and bounds exhaustion produce `status="exhausted"` with a reason; they do not produce `solved` or a feasibility certificate.

## Goal, feasibility, and alternatives

Goal satisfaction is read from explicit goal predicates against the candidate state. The planner does not infer reward from a transition name or scalar score. A reached goal is a solved **candidate** only if the complete path is available, every transition is current and admissible, and the path has a complete required-horizon manifold projection. Missing projection or an incomplete horizon is `unknown`, not feasible.

The existing native manifold projector is the sole feasibility authority. For every complete candidate path, compare `retained`, `lost`, and `escape` residual shapes against the same target manifold. Discard paths that violate hard constraints. Among feasible paths, minimize the projector's intervention measure; preserve all distinct paths tied at the minimum. Goal priority may break only an exact equal-intervention tie. Do not add arbitrary reward, probability, or cost terms into an uncalibrated scalar sum. When no path is yet projected, leave it `unresolved` and request the contractually permitted refinement through the funded manifold path; do not rank it as feasible.

An uncertain transition remains a separate branch with its envelope and evidence. A model confidence value is not a probability of goal success unless separately calibrated and registered. If feasible and unresolved alternatives coexist, keep both in the result; System 2 may only reopen a verified feasible candidate, and must retain the unresolved alternatives as uncertainty.

## Terminal states

The request has one terminal outcome:

- `solved`: at least one complete, current, admissible, manifold-feasible candidate path reaches the goal. Return tied minimum-intervention candidates and their provenance.
- `exhausted`: the bounded frontier is closed by depth, expansion, budget, deadline, or no admissible successors without a solved candidate. Include the exact reason and counts.
- `unknown`: a required model, transition, goal predicate, state identity, or complete manifold projection is missing or stale, so the search cannot distinguish success from failure.
- `model_stale`: source epoch, model epoch, goal epoch, or manifold epoch changed during planning. Cancel all pending debits and candidate reopen tokens; no candidate can be reopened from that request.

A stale change takes precedence over a previously found but not yet arbitrated candidate. The planner never claims a real-world result. Only a matching post-action observation or exact verifier receipt can ground an executed candidate; the receipt identity and observed state must match the selected request and path step.

## E4.3 reopen boundary

E4.2 emits advisory `ImaginedPlanCandidate` records only. E4.3 may consume each candidate once into a new System-2 decision revision keyed by `(request_id, candidate_id, source_epoch, model_epoch, goal_epoch, manifold_epoch)`. Reopen rechecks the active goal, model version, transition chain, complete manifold projection, and hard action guards. Stale or mismatched candidates are canceled. Authorization remains the separate G3 token and names the exact action sink. Grounding is permitted only after the native sink receipt and matching observation; an imagined plan or successful callback alone does not establish observed world state.

## Frozen acceptance cases

- `test_two_step_delayed_reward`: finds the two-transition goal path although an immediate locally attractive transition does not reach the goal; no one-step greedy shortcut.
- `test_cycle_terminates`: a self-loop/repeated state key is deduplicated and the bounded request terminates.
- `test_missing_transition_unknown`: missing successor evidence returns `unknown` or an explicit exhausted reason, never an invented wait/path.
- `test_imagined_not_system_one`: emitted plan candidates retain imagined, unobserved provenance and cannot become System-1 candidates.
- `test_stale_model_replans`: a model/goal/manifold/source epoch change cancels the old candidate and requires a new request under the new identity.
- `test_frontier_bound`: no execution can exceed depth 8 or 256 unique expansions.
- `test_every_expansion_funded`: each unique expansion has exactly one matching successful same-epoch debit; denied/unfunded states produce no successor expansion.
- `test_same_state_model_epoch_dedup`: duplicate state keys deduplicate within one model epoch but remain distinct across model epochs.

The public planner contract is opt-in under `CognitionPlannerPolicy.enabled=0`. No default profile activates planner search or imagined arbitration.
