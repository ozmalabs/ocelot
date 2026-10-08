# Live runtime closure-entry replay v1 results

## Result

The source-locked capture intercepted all 15 primary `run_rules` calls on the selected route: ten in request one and five in request two. All 15 call-entry graph/rule payloads decode, match their hashes, and pass the independent graph/node/edge checks. The capture reproduces the v1.6 task projection, replies, final graph digest, and behavioral counter rows; its source lock is stable before and after collection.

The replay restored every graph exactly and every rule table with match-clause order preserved, then ran each captured call once with its original progress cap. The independent analyzer's per-rule metric-cell exact fraction is 50.5%; exact total parity fails. For request one, candidate tests are 82,009 replayed versus 74,175 live (+7,834, +10.6%), Term evaluations 887,620 versus 803,675 (+83,945, +10.4%), and rule enumerations 29,247 versus 26,619 (+2,628, +9.9%). For request two, candidate tests are 43,650 versus 36,021 (+7,629, +21.2%), Term evaluations 452,204 versus 373,832 (+78,372, +21.0%), and rule enumerations 13,808 versus 12,521 (+1,287, +10.3%).

The scheduler trace identifies a concrete state omission. In request one, live calls two and three select 1,272 and 927 rules; replay from fresh substrates selects all 2,357 on both calls. Across requests, the live scheduler selected 26,619/12,521 rules, versus 29,247/13,808 in replay. Graph and rule bodies alone do not restore the persistent dirty-rule scheduler state. The replay binding also clears `mutation_protected` on installed rules; 2,356 of 2,357 rules are protected in the first request state and three rules carry rule-edit effects, so this remains a further fidelity caveat rather than an excluded concern.

## Evidence chain

- [Capture protocol](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_STATES_V1_1_PREREG_20261004.md)
- [Capture runner](../../../evaluation/substrate_capability/live_runtime_closure_entry_states_v1_1.py), [lock](../../../evaluation/substrate_capability/live_runtime_closure_entry_states_v1_1_lock_20261004.json), [capture manifest](../../../evaluation/reports/live_runtime_closure_entry_states_v1_1_20261004.json), [capture analysis](../../../evaluation/reports/live_runtime_closure_entry_states_v1_1_analysis_20261004.json), and [compressed call states](../../../evaluation/reports/live_runtime_closure_entry_states_v1_1_payloads/)
- [Replay protocol](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V1_PREREG_20261004.md)
- [Replay runner](../../../evaluation/substrate_capability/live_runtime_closure_entry_replay_v1.py), [lock](../../../evaluation/substrate_capability/live_runtime_closure_entry_replay_v1_lock_20261004.json), [raw replay](../../../evaluation/reports/live_runtime_closure_entry_replay_v1_20261004.json), and [independent analysis](../../../evaluation/reports/live_runtime_closure_entry_replay_v1_analysis_20261004.json)

## Next gate

Add an opt-in native scheduler checkpoint that exports/restores the per-rule dirty vector, per-rule dirty-node sets, incremental cursors, edge-delete version, and mutation-protection metadata. First prove checkpoint/restore parity on one call-entry state, then rerun the 15-call replay. Preserve any remaining mismatch as evidence for other hidden runtime state. This is a measurement and replayability result on one authored route, not a natural-task or scale estimate.
