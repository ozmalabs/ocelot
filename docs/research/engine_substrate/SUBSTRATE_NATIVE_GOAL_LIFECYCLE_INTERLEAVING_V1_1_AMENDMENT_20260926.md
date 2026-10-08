# Native Goal lifecycle interleaving v1.1 amendment

## Reason

The v1 capture showed that an event with two `for_goal` edges transitioned both Goals. The four native lifecycle rules now require that the matched Goal be the event's only distinct `for_goal` neighbor. This amendment repeats the original interleaving, omission, and ambiguous-owner controls against the updated seed.

## Confirmation gates

Preserve the three-worker source-stability and six-checkpoint positive interleaving gates. Missing-owner events must transition neither Goal. Ambiguous-owner events with two Goal links must also transition neither Goal. The native rule change must preserve all six positive per-owner state projections and terminal closure. Use v1.1 lock/raw/analysis paths and lock the amendment and changed seed.

## Limits

This confirms native rule semantics on the fixture. It does not prove thread safety, production scheduling completeness, or lifecycle behavior for event types outside the four guarded transition rules.
