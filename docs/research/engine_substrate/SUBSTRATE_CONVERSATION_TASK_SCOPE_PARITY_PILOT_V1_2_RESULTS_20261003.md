# Conversation task-scope parity pilot v1.2 results

Date: 2026-10-03

## Result

The v1.2 runner and independent analyzer pass across three fresh workers and four cases per worker: common-ground stress (4 task frames), and concurrent goals with 2, 4, or 8 task frames. All 12/12 final graph digests and all 198/198 checkpoint graph digests match between monolithic and globally reswept scoped closure. Goal status vectors match in every pair. The partition arm recorded 1,005 per-scope quiescence reports; every report showed zero progress and no pending deferred effects. The runtime reports `frame_notifications_complete: false` in every report, so the protocol compensates by sweeping every registered scope until a whole sweep makes no progress.

| Case | Task frames | Checkpoints across 3 workers | Monolithic median ms | Scoped median ms | Scoped calls |
|---|---:|---:|---:|---:|---:|
| Concurrent goals | 2 | 24 | 0.041 | 0.954 | 126 |
| Common-ground stress | 4 | 30 | 0.049 | 1.005 | 276 |
| Concurrent goals | 4 | 48 | 0.045 | 1.120 | 492 |
| Concurrent goals | 8 | 96 | 0.049 | 1.425 | 1,944 |

The scoped measurements include repeated matching and per-scope quiescence reports. This path still matches over the full graph on each scoped call. The rising call count and time show the cost of this conservative resweep schedule on the selected cases; they do not isolate asymptotic matching cost or compare against a genuinely factorized implementation. Do not interpret the timings as a fair optimized speed ratio.

## Interpretation and limits

V1.2 strengthens the v1.1 result from one two-goal case to authored 2/4/8-goal scales plus a four-frame shared common-ground stress case. It supports exact state preservation for this explicit ownership encoding and exhaustive resweep policy. Ownership roots are synthesized through the native node API, while `has_concept` membership edges are unchecked annotations in both arms because the loaded vocabulary does not admit these task-specific edges. The case set is authored, small, and from one conversation family. This does not establish learned frame discovery, natural workload prevalence, completeness of runtime access tracing, correctness under dynamic ownership changes or deletions, or computational factorization.

The capture's free-text claim boundary contains a typo listing a three-frame case; none was run. The actual locked case matrix and per-case `frame_count` values are 2, 4, and 8 for concurrent goals, and 4 for common-ground stress. See the [v1.2 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_2_AMENDMENT_20261003.md).

## Provenance

- [V1 method](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_METHOD_20261003.md)
- [V1.1 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_1_AMENDMENT_20261003.md)
- [V1.2 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_2_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2_lock_20261003.json)
- [Capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_2_20261003.json)
- [Analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_2_analysis_20261003.json)
