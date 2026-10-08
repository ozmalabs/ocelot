# Shared native facade serialization v1 protocol

## Question

When two `_AdapterNativeFacade` objects wrap the same PyO3 `Substrate`, do they obtain the same RLock and serialize calls across wrappers while a live `WorldAdapter.converse` transaction is active?

## Procedure

Run three fresh full-seed workers. Create a second native facade around the same raw native object and assert both facades initially share lock identity. Pause a conversation after Goal selection. Start contenders through public `tick`, adapter `inner`, adapter `s`, adapter `s._inner`, and the second facade. Instrument the shared lock, require every contender to attempt but none to enter while the conversation is paused, then release and require each operation to complete with no errors. Verify Goal/message/origin identity, terminal lifecycle, baseline reply, source stability, and thread joins.

## Claim boundary

This tests two facades created by the shared-lock constructor around one live PyO3 object in one schedule. It does not cover externally retained raw native references, direct facade `_native` access, arbitrary third-party wrappers, autonomous worker lock order, or all adapter operations.
