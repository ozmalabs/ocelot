# Metacognitive self-directed learning

Jabberwock now treats an executable `LearningPlan` as another revisable graph
program. The faculty is domain-neutral and integer-native: bodies and tasks
publish receipt summaries; metacognition reasons only over plan steps, causal
yield, context evidence, failure burden, cost, and typed revision edges.

The normal path is dormant. When a selected step exhausts its body-derived
evidence budget without new causal success, while another ready step has
productive evidence, the graph mints a `LearningPlanResidual` and recruits
System 2. Productive alternatives are materialized only during that sparse
deliberation boundary. This avoids a global policy sweep on every motor tick.

The current plan and its alternatives are complete four-coordinate integer
Pareto points. A unique verified frontier counterexample may redirect the
plan. Incomparable frontier points request a discriminating experiment rather
than using insertion order, a scalar score, or a fixed retry count. The
redirected step is held conditionally suspended until the target capability
both produces post-revision evidence and reaches mastery. A failed enacted
revision lazily materializes order N+1; unused reflective levels do not exist
on the hot path.

Revision memories are output-null and indexed by structural body signature,
capability identity, and goal. Recall can warm-start experiment allocation,
but cannot issue an actuator command or assert competence.

## Physical assay

The assay started from the retained v9 library described in
`SELF_DIRECTED_LEARNING_PLAN_RESULTS.md` and used a fresh PyBullet humanoid.
The executable result is
`results/learning_epochs/humanoid_autonomous_epoch_05_metacognitive.json`.

- Initial retained evidence exposed rolling at 0 successes in 259 attempts and
  prone forelimb support at 6 successes in 12 attempts.
- The graph raised one learning-plan residual and enacted one Pareto-supported
  revision. It made no discrimination request and did not scalarize the
  objectives.
- Prone forelimb support reached 16 successes in 27 cumulative attempts and
  crossed retained mastery.
- Only after that capability transition did the conditional revision reopen
  rolling. Rolling ended at 0 successes in 265 cumulative attempts.
- Retained mastery increased from six capabilities to seven in 50 physical
  actions.
- Runtime was 68 seconds on the host for the complete simulation and trace.

This is evidence of improved learning allocation, not evidence that rolling is
solved. It also shows why the held boundary must be a capability transition:
an earlier one-success reopening condition oscillated between steps and was
rejected by the physical assay.

## Verification

`tests/test_metacognitive_learning_migrated.py` covers unique Pareto revision,
incomparable-policy discrimination, causal conditional reopening, lazy order-N
materialization, integer-only cognition, output-null library round-trip, and
exact-body/exact-capability replay. The embodied-development suite verifies
that retained receipt counts enter the generic plan evidence contract.

## Consolidation and fresh-body replay

The first revision-bearing consolidation exposed an older identity bug. Both
`prone_forelimb_support` and `quadruped_support` share the goal
`support_discovery` and evidence kind `support_gain`. Supersession was keyed by
goal and body shape, so mastery of the first repeatedly superseded and
recreated the second capability's partial memory. A diagnostic boundary made
334 experience nodes in 1,000 commits.

Experience and capability memory identity is now the tuple of capability,
goal, evidence kind, and structural body signature. The focused duplicate-goal
test reaches an exact fixed point and preserves the independent partial
memory.

The corrected physical consolidation is recorded in
`results/learning_epochs/humanoid_autonomous_epoch_06_metacognitive_consolidated.json`.
It reproduced one residual, one enacted revision, and seven mastered
capabilities, then wrote
`results/learning_epochs/humanoid_metacognitive_motor_library_v1.json` with one
output-null revision memory. The complete 50-action simulation, consolidation,
and serialization took 67.7 seconds.

A new PyBullet body then loaded that v10 library for the five-action replay in
`results/learning_epochs/humanoid_autonomous_epoch_07_metacognitive_replay.json`.
It loaded exactly one metacognitive memory, conditionally suspended
`supine_prone_rolling`, and made the exact `prone_forelimb_support` capability
ready. It minted no new residual or revision and asserted no competence from
the memory. The replay took 12.2 seconds.

## Conditional reopening and retained reflective order

The first longer replay,
`results/learning_epochs/humanoid_autonomous_epoch_08_metacognitive_continuation.json`,
found that recalled memory had created a suspension edge without reifying the
typed revision node carrying its success baseline. Prone support reverified,
but rolling could not reopen. Replay now instantiates the same
`LearningPlanRevision` program as live deliberation, including its causal
baseline; it does not use a special host-side recall path.

`results/learning_epochs/humanoid_autonomous_epoch_10_metacognitive_reopen.json`
then demonstrated the full lifecycle on a fresh body: prone support earned its
new verification receipt, rolling reopened, and retained mastery rose to eight.
Continued zero-yield evidence produced another plan residual and promoted the
active reflective policy to order 2.

Reflective order is itself now retained practice. At a lifetime boundary, the
exact-body revision memory records the highest active policy order. The
93.6-second retained run in
`results/learning_epochs/humanoid_autonomous_epoch_11_metacognitive_order_retention.json`
recorded why order 2 was required: the recalled prone-support redirect
completed, a new rolling counterexample redirected to `prone_reach_and_pivot`,
and that enacted revision received its own counterexample. Consolidation
updated the output-null revision memory from order 1 to order 2.

Finally,
`results/learning_epochs/humanoid_autonomous_epoch_12_metacognitive_order_replay.json`
booted another fresh body in 12.4 seconds. Its single active metacognitive
policy began immediately at order 2, with one recalled enacted revision and no
new residual. Thus the system now retains not only a useful experiment
redirect, but the demonstrated depth of reflection required to manage it.

## Contextual negative knowledge

Failed redirects are now retainable without becoming permanent prohibitions.
A `MetacognitiveLearningCounterexampleMemory` records the exact body, source
capability, failed target, reflective order, and a relational set of every
mastered capability present when the revision failed. When the same source is
selected under exactly that mastery frontier, the target receives an
output-null `LearningPolicyCounterexampleHold` and is excluded from productive
alternatives. The hold is released as soon as the mastery set changes.

This avoids both catastrophic forgetting and a false global blacklist. The
memory round-trip, exact-context activation, changed-context release, and
duplicate-goal behavior are covered by focused graph tests. Two retained
physical attempts did not re-observe a failed redirect in their available
horizons, so they correctly stored no negative memory; no counterexample was
fabricated from an earlier JSON trace.
