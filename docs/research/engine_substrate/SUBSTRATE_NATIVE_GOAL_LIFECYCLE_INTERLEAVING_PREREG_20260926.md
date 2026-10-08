# Native Goal lifecycle interleaving probe preregistration

## Question

Do native Goal lifecycle rules preserve owner identity when two active Goals have interleaved events, and do they reject missing or ambiguous `for_goal` ownership?

## Protocol

- Three fresh full-seed processes construct one discourse state with two active Goals, each linked to its own origin request event.
- Interleave the explicit lifecycle sequence: A selection, B selection, B execution, A execution, A result, B result. After every event, run native rule closure and capture both Goal states, active/closed membership, transitions, and event owner edges.
- In a separate negative control, record a selection event with no `for_goal` edge and verify neither Goal transitions.
- In an ambiguity diagnostic, create a selection event explicitly linked to A, add a second `for_goal` edge to B, run native closure, and capture which Goal(s) transition. This measures current semantics; the preregistered safety expectation is that neither transitions until the event has exactly one owner.
- Lock source, seed, native build, runner, protocol, and commit fingerprints; verify start/end per worker and post-run state.

## Gates and interpretation

Capture validity requires three distinct worker PIDs, source stability, complete six-checkpoint captures, and the expected event schedule. Positive identity passes only if each transition is attached to the event's unique Goal and the six states match the interleaving oracle. Missing-owner rejection passes only if neither Goal transitions. Ambiguous-owner rejection passes only if neither Goal transitions. These semantic gates are reported independently so a valid capture can establish a substrate gap.

## Limits

This is a native-rule semantic probe using explicit owner links on fixture events. It does not test the live producer under thread concurrency, scheduler completeness, performance, task prevalence, or arbitrary rule sets.
