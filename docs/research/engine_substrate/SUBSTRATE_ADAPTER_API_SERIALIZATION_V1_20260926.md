# Adapter public API serialization v1 protocol

## Question

Does a single per-adapter RLock applied to public `WorldAdapter` methods serialize a live conversation against an independent public `tick()` call, while preserving the conversation's lifecycle and reply?

## Procedure

Run three fresh full-seed workers. Pause thread A after the live describe-scene selection event. Start thread B on public `tick()` and instrument lock acquisition to confirm it attempts entry while A is paused; verify A remains selected and B cannot enter the public method body before release. Release A, allow its conversation to complete, then allow B's tick to complete. Capture source fingerprints, exceptions, thread joins, Goal/message/origin identity, lifecycle terminal state, exact reply parity, and B's tick result.

## Claim boundary

This tests one pair of public adapter entry points on one adapter. It does not cover direct `s`/`inner` access, multiple adapters sharing a native object, every public method, autonomous native workers, all interleavings, or external effects. The lock is a Python adapter transaction boundary; it is not a redesign of PyO3's borrow model.
