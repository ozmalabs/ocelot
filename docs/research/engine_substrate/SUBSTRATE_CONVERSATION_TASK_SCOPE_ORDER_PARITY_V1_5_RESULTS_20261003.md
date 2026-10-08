# Conversation task-scope ordering parity v1.5 results

Date: 2026-10-03

## Result

V1.5 assigns three frame-sweep orders—ascending, descending, and outside-in—to three fresh workers each. Every worker executes the same four workload cells (2, 4, and 8 concurrent goals plus four-frame common-ground stress) in monolithic, scoped-trace-off, and scoped-trace-on arms. Independent analysis verifies 36 paired cases, 594 monolithic/scoped checkpoint comparisons, 36/36 final graph matches, 594/594 checkpoint matches, and trace-on/off parity for every scoped checkpoint. Each schedule policy therefore passes all 12 worker/case rows and 198 checkpoints. The 1,005 per-scope quiescence reports per schedule show zero progress and no pending deferred effects; notification completeness remains false and every scheduled frame is still revisited.

| Scope order | Paired cases | Checkpoints | Final matches | Monolithic candidate visits | Scoped candidate visits | Candidate ratio | Term ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ascending | 12 | 198 | 12/12 | 6,024 | 56,286 | 9.34× | 11.18× |
| Descending | 12 | 198 | 12/12 | 6,024 | 53,640 | 8.90× | 11.18× |
| Outside-in | 12 | 198 | 12/12 | 6,024 | 55,059 | 9.14× | 11.15× |

Across the complete panel the traced scoped arm records 153,564 observed access occurrences: 148,380 touch one task-owned endpoint and shared/unowned state; 5,184 remain within one frame; none directly join different owned frames. These traces remain partial. Scope path counters record 34,920 full-fallback matcher invocations and zero local-owned-edge or Microtheory-seeded invocations across all schedules.

## Interpretation

The exact state result is robust to three global scope visitation orders on this authored workload. It does not prove the same binding application order as monolithic matching in general, because each scope call filters and batches bindings separately. It does establish that final and checkpoint graph state is invariant for these three schedules and cases. The work profile remains far above monolithic closure because each multi-edge conversation rule takes the full-fallback path. Order sensitivity and broad shared-state access therefore remain primary controls for any candidate-seeded multi-edge matcher.

This is not factorized execution or a speedup result. The scope implementation repeatedly searches the full graph; task ownership edges are measurement annotations, trace coverage is partial, and the workload is one authored conversation family. Next, prototype explicit typed anchor metadata for eligible multi-edge rules and candidate-pruned enumeration behind the existing fallback. Require ordered-binding/effect parity, exact graph parity under cross-frame and dynamic-owner controls, and separately measured candidate/Term work before considering engine adoption.

## Provenance

- [Method](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_METHOD_20261003.md)
- [Multi-edge candidate-index audit](SUBSTRATE_SCOPED_MULTI_EDGE_CANDIDATE_INDEX_AUDIT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_5.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5_lock_20261003.json)
- [Capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_5_20261003.json)
- [Analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_5_analysis_20261003.json)
