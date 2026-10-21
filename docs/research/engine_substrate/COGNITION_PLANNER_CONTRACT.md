# Cognition planner contract v1.1

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

### Complete-path projection profile

E4.2 composes the path DAG before it may mark a multi-step candidate feasible. Each `CognitionPlanPathArrival` is one path step and links to exactly one predecessor arrival (the root links to a request-owned `CognitionPlanPathOrigin`), one current `CognitionPlanTransition`, and one destination frontier. A goal candidate names one terminal arrival; its ancestry is therefore one ordered path, even when state frontiers are shared. The planner keeps at most `maximum_path_arrivals` (default 4096) per request. Reaching that cap closes the request as `exhausted/path_arrival_limit`; it never drops unrecorded routes and continues as if the candidate set were complete.

The existing `FutureManifoldProjection` term is extended to accept an imagined candidate linked to one terminal path arrival. In action order, it reads each transition's `future_manifold_times`, `future_manifold_values`, `future_manifold_widths`, and `future_manifold_effort`. Each transition must provide a positive integer `future_manifold_duration`; its time coordinates must be exactly `1..duration`, its matrices must have equal row/column shapes, and all transitions in the path must use the request's `intervention_unit` and the same manifold dimensions. The term shifts each segment by the cumulative preceding duration and concatenates every row. It may truncate only after the request's `required_horizon`; it may not fill gaps, infer durations, carry values forward, or substitute a transition's terminal row for its missing trajectory. Missing, malformed, overlapping, or short paths return unresolved projection evidence, which the planner closes as `unknown/incomplete_path_projection`.

The path's intervention measure is the sum of all non-negative finite `future_manifold_effort` entries over the complete composed path, in the shared declared unit. This is the model's represented physical effort, not a confidence, reward, or planner-created weight. The native P4 feasible-set selector receives this value as the path candidate's `intervention`; only feasible complete paths with the minimum value are retained, and exact ties remain set-valued. An absent unit, mixed units, or missing effort makes the path unresolved rather than assigning zero effort. The native projection continues to own the full retained/lost/escape residual assessment against one target manifold.

`FutureManifoldProjection` retains its current `(episode, policy, source, field)` argument schema and field meanings. Its path-source extension adds `path_intervention` as a field result and reads path links only when `source` is an `ImaginedPlanCandidate` with exactly one `has_terminal_path_arrival` edge. Existing non-path source behavior remains byte-for-byte compatible. Work is bounded by the 8-step search cap and the 4096-arrival request cap; path matrix composition is linear in rows through the required horizon. Serialization uses ordinary graph nodes/edges and requires no new term variant.

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
