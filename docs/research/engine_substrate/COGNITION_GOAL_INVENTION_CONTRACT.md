# Goal regression and parametric process invention contract v1

Status: semantic freeze for P10.01–P10.E3. The policy is opt-in and disabled by default. A lifted process is a candidate schema, not a strategy or a solved task.

## 1. Lifted process representation

A lifted process retains a structural `expr_tree`, a typed binding environment, source schema IDs, and an `AntiUnifyWitness` whose template and per-example substitutions reconstruct every source expression exactly. A wildcard is a positional parameter, never a global variable name. Binding paths are scoped to one schema instance; no variable may capture another binding or cross a process/domain boundary.

Every parameter has an explicit type, range/shape constraint, and source witness. A size parameter is not inferred from a finite maximum seen in training. Index parameters require `0 <= index < size`; dimension and permutation parameters require the instantiated shape to match the target domain. Unseen-size use is allowed only when the symbolic constraint is proved and the native effect evaluator accepts the instance. Failed or unsupported instances remain candidates/unknown and are not executable.

## 2. Effect regression and verification

A requested goal is represented by a typed `ProcessGoal` descriptor: domain and kind, current source/model/frame epochs, initial-state identity, declared goal predicate or exact goal state, required effect, and resource limits. A `ProcessGap` is keyed by goal/request identity plus those epochs and records the missing typed effect, open/unknown status, current frontier, and bounded work counters. Goal identity does not collapse different domains, frames, predicates, or epochs.

Regression compares the current state with the declared goal and decomposes a typed missing effect only when the relevant native evaluator supports it. A candidate precondition must hold at the actual state; its predicted postcondition is checked by native effect application. A lifted or newly composed process is adopted only after fresh-state verification under the current epochs. Missing effect families, malformed bindings, unsupported predicates, or insufficient probes produce `unknown`/`needs_tool` or a synthesis interface request; they never become a guessed identity effect.

The goal frontier is bounded to depth 8, 256 unique expansions, the shared approved ThinkingBudget, and the phase's explicit candidate cap. State identity includes domain, frame, and model epoch. Cycles deduplicate only within that identity. A stale source/model/frame/goal epoch cancels the request and all unverified candidates; work must restart under a new identity.

## 3. Strategy discovery boundary

A strategy is a graph-held composition or constraint relation discovered from ordinary process applications, failed/successful traces, and verified effects. No Python puzzle solver, placement recipe, hand-authored sequence, answer trace, or held-out solution may enter the treatment graph. Python remains limited to constructing worlds and scoring externally observed outcomes. The committed greedy solver is a comparator only.

An unmet effect with no covering verified process creates a typed `ProcessGap` and may request a bounded `GoalInventionPolicy` rung. An unsupported gap creates an explicit `SynthesisInterfaceRequest`/`needs_tool` status with missing effect type and evidence; it does not silently call code synthesis. A new program candidate, if later connected, must pass the existing program verifier and current observation checks before use.

## 4. Provenance, budgets, and defaults

Every lifted schema records its witnesses, parent schema IDs, binding constraints, domain, effect evaluation, source/model/frame epochs, verification receipt, cost, and provenance. Deduplication is allowed only for exact effect equality within the same domain and epoch. Probe-relative similarity retains both candidates.

`GoalInventionPolicy`, `ProcessLiftingPolicy`, and `StrategyDiscoveryPolicy` default disabled and are added only to the cognition-on profile. A targeted rung uses the shared ThinkingBudget and one unique request/debit identity. Denial, timeout, expiry, stale evidence, or unsupported evaluation restores the prior policy state and leaves the frontier unresolved without spending twice.

## 5. Acceptance and controls

- `test_lift_preserves_bindings`: AntiUnifyWitness plus substitution reconstructs each source tree and preserves binding identity.
- `test_unseen_size_preconditions`: symbolic size/index constraints accept valid unseen sizes and reject out-of-range bindings before evaluation.
- `test_goal_gap_mints_interface`: a genuinely missing typed effect creates a bounded ProcessGap/interface record; no strategy or answer is injected.
- `test_no_handwritten_strategy_input`: treatment graph inputs contain worlds, held primitives, goals and observations only, with no placement recipe, solution trace, or target process.
- P10.02 adds unseen-size native effect verification, bad-binding refusal, and lifted provenance.
- P10.03 adds funded goal regression, denied-rung restoration, and verifier-preserving program candidates.
- P10.04 adds task-trace strategy discovery, delayed-progress controls, odd-wall breaker use, and graph-decision-only traces.

Controls include variable capture, missing bindings, out-of-range indices, mismatched dimensions, stale epochs, duplicate request/debit IDs, denied budget, unsupported effect families, cycles, held-out target leakage, and attempted Python strategy injection. No control may be converted to a passed identity or guessed solution.

## 6. P10.02 native lifting subset

The first executable lifted-template grammar is deliberately finite: `cycle(size,start,length)`, `swap(size,i,j)`, and recursive `compose`, `inverse`, and `commutator`. The anti-unification witness must show that every wildcard capture used for size or cycle length equals the corresponding size in every source domain. Captures that vary for another reason, missing paths, malformed trees, non-permutations, and unsupported operators return unknown. Target sizes must be strictly greater than both source sizes and no greater than the policy cap (16 in the seed); native constructors independently cap size at 256. The graph stores a lifted ProcessSchema only after the native constructor returns a concrete process and the target domain probe fingerprint evaluates. This subset does not claim lifting arbitrary programs or every process family.
