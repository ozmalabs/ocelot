# Conversation task-scope parity pilot v1.1 amendment

Date: 2026-10-03

V1.1 preserves the v1 workload, pairing, closure schedule, and parity gates. It strengthens the capture by storing each per-scope quiescence report so the independent analyzer can verify the result directly. The analyzer now requires both scopes at every checkpoint, zero progress on each quiescence call, no pending deferred effects, and an explicit `frame_notifications_complete: false` value. This makes the conservative all-frame resweep policy visible and prevents an incomplete-notification API flag from being misreported as complete.

The three-worker v1.1 run passes with 24/24 checkpoint state matches, 3/3 final-state matches, matching goal statuses, and all 48 scope quiescence records showing zero progress and no pending deferred effects. The engine still reports notifications incomplete; the experiment manually revisits every registered scope until a global sweep is quiescent. No workload or success threshold changed. V1 remains preserved, including its first self-check failure and original capture.

Artifacts: [v1.1 method](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_METHOD_20261003.md), [runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_1.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1_lock_20261003.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_20261003.json), and [analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_1_analysis_20261003.json).
