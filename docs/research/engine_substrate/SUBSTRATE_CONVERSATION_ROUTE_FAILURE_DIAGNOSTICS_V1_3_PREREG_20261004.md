# Conversation route failure diagnostics v1.3 preregistration

Date: 2026-10-04

## Intervention

The v1.2 export showed that the active graph-resident composer rule omits
`Goal --comprehends--> Message`, although the Python reference composer
includes it and the live action requires it to find the request-owned Goal.
Add that relation to `seeds/composer_comprehension_graph.json`'s generated
effect list. No other rule or route behavior is changed.

## Verification

Repeat the same fixed five-prompt sequence in two fresh workers under a lock
that explicitly includes the modified seed and dynamic scene/language
dependencies. Verify from the active rule export that the relation effect is
present; verify the newly minted describe Goal is linked to the current inbound
Message; record the describe action's route/reply and final route/reply. The
capture gates remain source stability, two distinct workers, five prompts, and
resolved Message IDs. The independent analyzer must recompute the intervention
checks from the retained traces.

## Limits

This is a two-worker intervention check on one authored task order. It can
establish that the missing ownership edge is restored in this fixture and that
the scene action no longer falls through there. It does not establish
counterbalanced behavior, task correctness across independently authored
prompts, frame locality, or general capability.
