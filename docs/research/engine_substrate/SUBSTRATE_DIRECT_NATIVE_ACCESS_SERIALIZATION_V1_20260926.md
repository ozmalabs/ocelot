# Direct native-access serialization v1 protocol

## Question

Do adapter graph handles `inner`, `s`, and `s._inner` share the same transaction lock as public `WorldAdapter` methods, including direct native calls concurrent with `converse`?

## Procedure

Run three fresh full-seed workers. Pause a describe-scene `converse` after Goal selection. Start four separate threads that call public `tick()`, `inner.node(agent)`, `s.node(agent)`, and `s._inner.node(agent)`. Instrument the common RLock to observe each contender attempting acquisition and then entering after the active conversation releases it. Require no contender to enter while A is paused, a correct A lifecycle and baseline reply, successful completion of all four operations, no errors, joined threads, and source-stable fingerprints.

## Claim boundary

This covers these adapter-owned handles in one controlled schedule. It does not cover native handles retained before facade installation, direct access to the internal facade target, multiple adapters sharing one PyO3 object, external PyO3 callers, autonomous worker lock ordering, or all cross-entrypoint schedules.
