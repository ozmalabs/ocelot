# Live runtime dirty-rule entry audit v1 results

## Result

The source-locked audit records all 15 primary `run_rules` entries on the selected two-request route and passes parent task, reply, final graph, behavioral counter, and source-lock parity. Its v1.1 independent amendment passes all gates.

Before each of the five one-pass calls, `dirty_rule_count` exactly equals that call's `scheduler_selected_rules` count. In the ten two-pass calls, the entry dirty count is the initial selection; selected-rule totals exceed it by 5,661 rows in request one and 1,993 in request two. Those nonnegative residuals are selections in the later pass. The exported dirty-name rows equal each native dirty count, with every row either mapped to a local slot or explicitly listed as ambiguous. Thus the dirty-rule vector explains initial rule selection and the multi-pass work trace is consistent with rules becoming dirty during the call.

The work evidence points to dirty-rule bits as the principal source of the fresh-replay overcount, but not the only hidden state that may matter. Replay still lacks per-rule dirty-node sets, incremental cursors and edge-delete version, and mutation-protection metadata; those must be preserved before exact counter parity can be expected.

## Evidence

- [Protocol](SUBSTRATE_LIVE_RUNTIME_DIRTY_RULE_ENTRY_AUDIT_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1.py), [capture lock](../../../evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1_lock_20261004.json), and [capture](../../../evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_20261004.json)
- [Independent v1.1 amendment](SUBSTRATE_LIVE_RUNTIME_DIRTY_RULE_ENTRY_AUDIT_V1_1_AMENDMENT_20261004.md), [analysis lock](../../../evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1_1_analysis_lock_20261004.json), and [analysis](../../../evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_1_analysis_20261004.json)

## Next gate

Add opt-in native checkpoint/restore for dirty-rule bits and mutation-protection metadata, then measure whether the same call-entry replays reproduce first-pass and later-pass selected-rule counts. Add dirty-node sets, cursors, and edge-delete version if the remaining per-rule counter gaps require them. Preserve the current one-route scope limit.
