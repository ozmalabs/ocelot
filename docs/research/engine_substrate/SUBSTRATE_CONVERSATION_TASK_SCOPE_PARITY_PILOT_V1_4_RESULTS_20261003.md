# Conversation task-scope parity pilot v1.4 results

Date: 2026-10-03

## Exact state and trace parity

The source-locked v1.4 capture compares three arms across three workers and four conversation workloads: monolithic closure, globally reswept task scopes with tracing off, and the same scoped schedule with runtime tracing on. All 12 monolithic/scoped pairs and all 12 scoped trace-off/trace-on pairs have identical final graph state and checkpoint state. Corrected independent analysis verifies 198 checkpoint comparisons, matching goal statuses, all 1,005 per-scope quiescence reports with zero progress and no pending deferred effects, and zero dropped runtime trace rows. The runtime continues to report `frame_notifications_complete: false`; every scope is revisited until a whole sweep makes no progress.

## Measured computation

| Workload | Frames | Monolithic candidate visits | Scoped candidate visits | Monolithic Term evaluations | Scoped Term evaluations | Scoped calls |
|---|---:|---:|---:|---:|---:|---:|
| Concurrent goals | 2 | 357 | 1,107 | 1,212 | 4,041 | 126 |
| Common-ground stress | 4 | 417 | 2,289 | 1,308 | 8,067 | 276 |
| Concurrent goals | 4 | 1,158 | 6,750 | 3,480 | 23,526 | 492 |
| Concurrent goals | 8 | 4,092 | 46,140 | 11,184 | 156,444 | 1,944 |
| **Total** |  | **6,024** | **56,286** | **17,184** | **192,078** | **2,838** |

The conservative scoped route therefore performs 9.34× the candidate visits and 11.18× the Term evaluations of monolithic closure on this panel. Its current implementation repeatedly matches over the full graph and includes explicit quiescence probes. This is direct evidence that restricting post-match bindings by scope does not yet yield cheap factorized closure in this workload.

The source and native path counters identify why: all four loaded discourse lifecycle rules have four match edges, while the current optimized scope paths cover a single-edge pattern (and the specialized one-edge `has_concept` Microtheory seed). Across this panel, 11,640 matcher invocations use `FullFallback`; `LocalOwnedEdge` and `MicrotheorySeed` each record zero. Candidate seeding for the owned Goal variable is a plausible next optimization, but preserving global binding/effect order and shared-state dependencies must be demonstrated before adopting it.

The separate traced scoped arm records 51,246 observed event occurrences: 49,500 have one task-owned endpoint and one shared/unowned endpoint, and 1,746 are within one frame. No observed event directly links differently owned task nodes. These are partial runtime traces; they do not prove access completeness. Tracing preserves exact state on this panel, but traced timing is not used for a speed comparison.

## Limits and next gate

This establishes semantic parity and exposes the repeated work for one authored conversation family at 2/4/8 concurrent goals plus one 4-frame stress case. Ownership edges are unchecked measurement annotations; the partition schedule globally revisits all frames; matcher visits are not localized; and natural-task prevalence is unmeasured. It does not establish a general partition contract, safe dirty-only notifications, dynamic ownership/deletion behavior, learned boundaries, or scaling advantage.

The next engine gate should use these work counters as a baseline while testing explicit candidate pruning or per-frame indexes, with independent read-scope validation and omitted-cross-frame negative controls. Require exact graph/goal parity and count matcher work separately from scope calls, quiescence probes, interface construction, and notification overhead. Do not infer a speedup from this parity result.

## Provenance

- [V1.3 source-lock amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_3_AMENDMENT_20261003.md)
- [V1.4.1 analyzer correction](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_4_1_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4_lock_20261003.json)
- [Capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_20261003.json)
- [Original analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_analysis_20261003.json)
- [Corrected independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_4_1.py)
- [Corrected analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_1_analysis_20261003.json)
