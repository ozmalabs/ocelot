# Conversation task-scope parity pilot v1.4.1 analysis amendment

Date: 2026-10-03

The v1.4 capture and runner are unchanged. Review of its first independent analysis found a variable-shadowing bug: the displayed checkpoint count was computed from the last quiescence dictionary instead of the checkpoint list, yielding 204 rather than the raw capture's 198. V1.4.1 is an independent analyzer-only correction. It computes checkpoint counts from all three captured arms, requires the exact expected count per case (10 for common-ground stress and 4×goal-count for concurrent-goal cells), and additionally reports monolithic and scoped matcher/Term work by case.

The corrected analysis passes with 198 checkpoints, 12 final-state matches, and zero errors. Its work totals are 6,024 monolithic versus 56,286 scoped candidate-pair visits (9.34×), and 17,184 versus 192,078 Term evaluations (11.18×). The traced scoped arm remains state-identical to the untraced scoped arm. V1.4's original analysis artifact remains preserved; v1.4.1 writes a separate corrected JSON analysis over the same source-locked raw capture.

Artifacts: [corrected analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_4_1.py), [corrected analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_1_analysis_20261003.json), [v1.4 capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_20261003.json), and [v1.4 lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4_lock_20261003.json).
