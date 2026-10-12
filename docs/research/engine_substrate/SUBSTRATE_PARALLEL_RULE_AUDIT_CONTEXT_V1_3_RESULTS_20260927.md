# Parallel rule-audit context v1.3 results

Date: 2026-09-27 local

## Outcome

The three-worker source/native lock passed: every worker's start and finish fingerprints and the post-run fingerprint match the saved lock. Native matcher attribution passes its dedicated gate across all six request intervals. For each request, candidate tests partition exactly into verified per-rule/per-clause work and explicitly unattributed work; no out-of-arity rows or attributed rows for ambiguous IDs remain.

The capture does **not** pass the full repeatability or task-semantic gate. Two workers reproduce the earlier global totals and semantic graph. One worker ends with two fewer nodes and three fewer edges, and its matcher candidate count is correspondingly lower. Replies, six-event order, distinct Goal identity, lifecycle, serialization, and pause behavior reproduce. Request A still returns the gap response rather than the exact baseline description; B returns the expected description.

## Measured matcher work

| Request | Candidate tests across 3 workers | Median | Unattributed per worker |
|---|---:|---:|---:|
| A | 677,795; 584,723; 677,795 | 677,795 | 381 (0.0562% of the matching worker total) |
| B | 842,748; 710,583; 842,748 | 842,748 | 419 (0.0497%) |

The two repeated graph states match the v1 global totals exactly. The smaller graph state does not: A is lower by 93,072 candidate tests and B by 132,165. Across verified attributed work, two-edge patterns account for 84.58%, one-edge patterns 14.69%, and all larger arities together about 0.73%. The largest named contributors are three recognition rules (`recognise_a_thing_that_moves_itself`, `recognise_a_thing_that_stays_put`, and `recognise_a_counter`), followed by `curiosity_targets_ambivalent_nodes`. These are fixture-specific request-lock counts, not CPU-time estimates or natural-task prevalence.

## Attribution correction

V1.2 showed that a numeric audit ID could be registered against more than one matcher shape during a request interval. V1.3 permanently marks a reused ID ambiguous, retracts its earlier attributed candidate rows into the unattributed bucket, and rejects later attribution under that ID. The conflict count is stable across workers (8 ambiguous IDs for A, 9 for B). The exact conservation and valid-arity checks pass in all six intervals.

## Gate status and limitations

The analyzer passes 57/60 checks. The three failed checks are final semantic graph reproduction across workers and the two comparisons of the smaller worker's totals against v1. The dedicated attribution gate passes; overall capture integrity does not, because work and final graph state vary across one repeat. The reply-quality gate also remains failed for request A. The result therefore supports exact attribution for the observed intervals while reporting a 13.7% A and 15.7% B range from one lower-work replicate; it does not establish a deterministic per-request cost.

The initial v1.2 run was rejected because `world_adapter.py` changed during worker 3. Its raw files remain preserved and excluded. A separately documented analyzer-only correction fixed the v1.3 top-rule report to group by request; raw capture and worker fingerprints are unchanged.

## Artifacts

- [Preregistration](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_3_PREREG_20260927.md)
- [Implementation amendment](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_3_AMENDMENT_20260927.md)
- [Source/native lock](../../../evaluation/substrate_capability/parallel_rule_audit_context_v1_3_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_3_workers_raw_20260927.json)
- [Driver record](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_3_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_3_analysis_20260927.json)
- [Worker](../../../scripts/substrate_parallel_rule_audit_context_v1_3_worker.py), [driver](../../../scripts/substrate_parallel_rule_audit_context_v1_3.py), and [analyzer](../../../scripts/analyze_substrate_parallel_rule_audit_context_v1_3.py)

## Forensic follow-up

A six-worker exploratory graph capture subsequently reproduced the high-work semantic graph and request totals in all six runs. Raw differences were only `runtime_s`/`ts` on four `SystemModel` nodes. The one lower-work v1.3 state therefore remains an unresolved 1/9 observation; its original graph records were not retained. See [variance replay v2](SUBSTRATE_LIVE_TASK_GRAPH_VARIANCE_V2_RESULTS_20260927.md) and its [six-worker structural diff](../../../evaluation/reports/substrate_live_task_graph_variance_v2_20260927.json).
