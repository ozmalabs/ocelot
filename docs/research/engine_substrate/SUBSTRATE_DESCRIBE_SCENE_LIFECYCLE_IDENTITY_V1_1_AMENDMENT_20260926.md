# Describe-scene lifecycle identity v1.1 amendment

## Reason

The v1 baseline confirmed that two sequential requests reuse one parent Goal, with no origin event edge or lifecycle events. The bounded implementation now gives each live request a cloned scene view, passes the actual inbound Message to the authored comprehension rule, and links the rule-minted parent Goal to that Message. Host wiring identifies the unique newly minted Goal by the explicit `comprehends` edge rather than global Goal ordering. The parent is the lifecycle owner; per-percept `produce_utterance` subgoals are internal decomposition and do not receive discourse lifecycle events.

## Changed protocol gates

- Preserve three fresh source-stable full-seed workers and two sequential requests against one attached base scene.
- Require distinct parent Goals, exactly one matching parent per inbound Message, each parent comprehending and originating in only its own Message/event, and no cross-turn owner links.
- Require exactly one ordered `selection`, `execution`, `action_result` sequence per parent; each event must link only to that parent. Each parent must resolve, be closed, and be absent from the active set.
- Require each parent to own three request-local utterance subgoals in the authored fixture and to describe a distinct request-scene view linked to the shared source scene.
- Keep the v1 failure capture and analysis unchanged. The confirmatory v1.1 artifacts use new filenames and a lock that includes this amendment.

## Limits

This establishes only sequential identity and lifecycle behavior on the tested attached-scene route. It does not establish thread/concurrent safety, other production routes, external-effect authorization, natural-task prevalence, or scaling. Rule closure, scene copying, faculty construction, and utterance production are all included in observed turn time.
