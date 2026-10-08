# Live multi-Goal origin identity probe

**Question:** does the live conversation path preserve a distinct Goal-to-origin mapping across two same-recipient instruction turns in one session, even though it emits no downstream lifecycle events?

In three fresh processes, create `WorldAdapter(seeds=())`, load the full seed set, and send two identical `Check the pressure.` instructions from speaker `alice` through `WorldAdapter.converse`. Capture the inbound Message, DiscourseEvent, same-recipient edge, Goals whose `source` is `conversation`, origin/comprehension links, associated Deliberations, operation lifecycle event counts, construction/boot/turn timing, and PIDs.

Require exactly two instruction events and two conversation action Goals; a one-to-one mapping where each Goal comprehends exactly its corresponding inbound Message and originates in exactly its corresponding DiscourseEvent; no cross-origin links; same recipient on both events; no `selection`, `execution`, or `action_result` DiscourseEvents. Report other Goals separately. This is a positive origin-provenance check, not a claim that downstream action lifecycle identity is implemented. The repeat protocol follows the prior one-turn discovery; the prior capture is not pooled.
