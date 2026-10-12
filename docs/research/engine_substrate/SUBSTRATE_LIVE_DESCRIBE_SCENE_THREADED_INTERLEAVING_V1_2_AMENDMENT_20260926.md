# Live describe-scene threaded interleaving v1.2 amendment

## Question

Does the new per-adapter reentrant conversation lock serialize two simultaneous `WorldAdapter.converse` calls on one adapter, preserve same-thread reentry, and restore both baseline replies after the v1.1 PyO3 borrow failure?

## Procedure and gates

Use three fresh processes and the same A/B describe-scene route. Pause A immediately after its selection event; start B and instrument the lock boundary to confirm B attempts acquisition while A is paused. Confirm B has not emitted a selection before A is released. Then require sequential A and B lifecycle event blocks, distinct Goal/message ownership, terminal closure, two baseline replies, and joined threads without exceptions. The capture also times ordinary sequential calls, but this small route-specific sample is descriptive overhead evidence only. Source hashes must remain stable throughout workers and after capture. This is an amended confirmation of v1.1, not a claim of general adapter thread safety.
