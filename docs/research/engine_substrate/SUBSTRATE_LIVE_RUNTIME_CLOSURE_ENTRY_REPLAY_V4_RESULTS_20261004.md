# Live runtime closure-entry replay v4 results

## Result

The native `RuleSchedulerCheckpointV1` serializes and restores per-rule dirty bits, per-rule dirty-node sets, per-edge-type cursor positions and cursor deletion versions, global edge-deletion version, and `any_mutation`. With the existing graph payload plus ordered rule import (including `mutation_protected`), replay reproduces the locked live work counts exactly for all 15 primary closure calls across both requests. Independent analysis reports 13,376/13,376 metric cells exact (100.0%). All six aggregate totals match for both requests: candidate tests/pairs, Term evaluations, rule enumerations, where evaluations, and where rejections. The earlier graph/rule-only replay was 10.6–21.2% high on candidate work; restoring the scheduler state closes that gap on this route.

The capture retains task, reply, final graph digest, and behavioral-counter parity with the v1.6 parent. The v2 capture analyzer validates all 15 scheduler payloads and dense vector sizes. Replay graph comparison is exact in 13/15 states. In the remaining two, only `nodes/25055/attrs/ts` differs, by `2.384185791015625e-07` (one binary64 ULP); the v4 amendment records this explicitly and accepts only structural equality plus at-most-one-ULP float deltas. Rule and scheduler round-trips are exact in all 15. The raw report therefore does not claim byte-exact graph persistence.

## Interpretation and limits

This is a positive determinism result for one authored two-request route, not a general tractability, natural-workload, or scaling theorem. It establishes that the measured replay gap was caused by omitted mutable scheduler state in these call-entry snapshots. Evaluation-cache contents and closure-affecting configuration are not in `RuleSchedulerCheckpointV1`; their relevance outside this route is untested. Graph persistence also has a demonstrated one-ULP timestamp round-trip loss.

## Artifacts

See [capture preregistration](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_STATES_V2_PREREG_20261004.md), [replay amendment](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_REPLAY_V4_AMENDMENT_20261004.md), [capture runner](../../../evaluation/substrate_capability/live_runtime_closure_entry_states_v2.py), [capture analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_entry_states_v2.py), [replay runner](../../../evaluation/substrate_capability/live_runtime_closure_entry_replay_v4.py), [replay analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_entry_replay_v4.py), [capture](../../../evaluation/reports/live_runtime_closure_entry_states_v2_20261004.json), [capture analysis](../../../evaluation/reports/live_runtime_closure_entry_states_v2_analysis_20261004.json), [replay](../../../evaluation/reports/live_runtime_closure_entry_replay_v4_20261004.json), and [replay analysis](../../../evaluation/reports/live_runtime_closure_entry_replay_v4_analysis_20261004.json).
