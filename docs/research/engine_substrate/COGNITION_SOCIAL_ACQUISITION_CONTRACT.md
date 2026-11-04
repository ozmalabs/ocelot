# Social acquisition and explain/rebuild contract

**Status:** frozen interface semantics for Phase 12. This contract does not
claim that imitation, social acquisition or process explanation is already
implemented. Runtime decisions remain Rust graph rules; host code may only
translate observed world events and read receipts.

## Evidence sources and attribution

Every social input is a source-bound episode with a stable `episode_id`,
`schema_version`, `source_epoch`, `owner_id` (the learner), `observer_id`,
`actor_id`, `actor_body_id`, and `learner_body_id`. It also declares
`source_kind`: `witnessed_interaction`, `directed_demonstration`, or
`instruction`. These sources stay distinct through candidate construction and
adoption. A witnessed interaction does not require a teacher marker; a
demonstration is intentionally directed to the learner; an instruction is a
symbolic constraint and is never itself an observed execution.

Observed actions are ordered `SocialActionObservation` records attached to
their episode. Each has a source event identity, actor, action token, target,
order index, observation epoch and visibility state. A separate
`SocialObservationCoverage` states which interval or event channels were
visible. `missing`, `occluded`, `ambiguous` and `not_observed` mean unknown;
they never mean that no action occurred. The adapter preserves event order and
reports only what the world exposed. It cannot fill gaps from a desired answer,
infer a successful outcome from the task prompt, or compile traces into an
executable program.

Intent is represented separately as an attributed hypothesis with actor,
episode, evidence references, confidence/status and source epoch. An actor's
goal is not the learner's goal. Intent may guide which witnessed events are
grouped as a candidate, but it cannot supply unobserved actions or prove an
effect. Conflicting intent hypotheses and contradictory observations remain
separate evidence.

## Body and frame correspondence

Action tokens are interpreted in the actor's body and frame. Transfer to the
learner requires a graph-resident `SocialBodyFrameMap` with explicit source and
target body IDs, source/target frame IDs and epochs, declared action mapping,
bidirectional verification status and a distinguishing set appropriate to
the declared map. Missing, stale, one-way, ambiguous or mismatched maps block
own-body trials and adoption. Name similarity or matching action labels alone
does not establish correspondence. A failed mapping remains unknown and may
not be repaired by the Python adapter.

## Candidate, verification and own grounding

Native rules may organize ordered observations into a bounded
`DemonstratedProcessCandidate`. It retains episode, actor, source action IDs,
coverage, map identity and uncertainty. It is not a `ProcessSchema`, learned
fact or executable strategy merely because an observed actor succeeded.

There are three distinct outcomes:

1. `ObservedActorOutcome` records only what happened to the observed actor.
2. `DetachedOwnModelVerification` records a funded, side-effect-free rollout
   in the learner's declared model. It can support model adoption but is not a
   physical or real-world own trial.
3. `OwnTrialReceipt` records an actual learner action and outcome, tied to the
   learner body, current frame, authorization and world epoch. Only this receipt
   can ground own execution or count as own-trial learning.

Candidate construction, detached verification and any consequential own action
must use bounded, funded graph requests with source/epoch identity and exactly
one terminal outcome. Actual action emission remains behind P5 host approval,
action arbitration and the existing time-indexed future-manifold safety
boundary. Social evidence cannot authorize an action or bypass a stop.

Adoption requires a current verified body/frame map, native own-model effect
verification on fresh discriminating probes, source and model epoch agreement,
and applicable existing process-adoption safety rules. Failed own-model
verification rejects the candidate. A candidate may be retained as
unverified evidence without promotion. Grounding is not inferred from
another actor's success, language agreement, confidence or detached rollout.

## Explain and rebuild

An explanation is produced through the ordinary language production stack and
has an explicit vocabulary/expressibility record. A rebuild receiver starts
from an isolated graph and receives only the explanation plus declared shared
primitive vocabulary. The receiver gets no source actor IDs, source AST,
process fingerprint, library entry, hidden evaluator answer or candidate
strategy. Ordinary graph acquisition constructs a receiver-owned candidate;
native verification compares its effects on fresh probes. Ambiguous or
incomplete explanations remain unresolved. The second-agent case uses the
same boundary. Explanation length, vocabulary coverage, exposure and probe
work are recorded separately.

## Evidence labels and evaluation boundaries

Keep `witnessed`, `directed_demonstration`, `instructed`, `detached_prediction`,
`own_trial`, and `verified_effect` as distinct evidence labels. Record learner
exposure opportunities even when no event is visible. The Phase 12 evaluation
must compare observation-only, demonstration, instruction and reward-only
families under equal declared evidence opportunities; shuffled, missing-step
and body-mismatch controls must not create unsupported adoption or own
grounding. No null adapter is scored as zero.

The registered Phase 12 task outcomes are still limited to its declared
synthetic supported interfaces. Passing them does not establish unrestricted
social understanding, reliable natural-language interpretation, human-level
teaching or broad physical imitation.
