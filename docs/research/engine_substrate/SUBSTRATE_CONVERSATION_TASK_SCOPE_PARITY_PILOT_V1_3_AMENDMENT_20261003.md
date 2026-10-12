# Conversation task-scope parity pilot v1.3 amendment

Date: 2026-10-03

V1.3 repeats the v1.2 panel with two reproducibility corrections. First, its source lock now includes `runners/dsl/src/term.rs` directly, alongside the reused panel runner, native extension/build manifest, and other execution sources. Second, the free-text claim boundary correctly describes the matrix, and the independent analyzer checks the exact case/count matrix plus each measured frame count: common-ground stress has four frames; concurrent-goal cases have 2, 4, and 8 frames.

No workload or parity threshold changed. The three-worker capture again passes 12/12 final graph matches, 198/198 checkpoint matches, matching goal statuses, and all per-scope quiescence checks. V1.2 remains preserved with its disclosed source-lock omission and claim-string typo; v1.3 is the preferred source-locked confirmation of this panel.

Artifacts: [v1.3 runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_3.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_3.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_3_lock_20261003.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_3_20261003.json), and [analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_3_analysis_20261003.json).
