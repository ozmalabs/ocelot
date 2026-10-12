# Live conversation task inference counters v1 results

**Result: the ten-worker task-diverse counter capture passes integrity and
repeat-parity gates.** All five authored `WorldAdapter.converse` task
conditions ran twice against the current provenance-checked default engine.
Each worker has one source-stable request observation; task-contract outcome,
reply, and action result repeat exactly within each pair. Eight of ten task
contracts pass: scene description, held self-knowledge, self-report, and
unknown-word clarification pass in both replicates; concern authoring fails in
both.

| Task condition | `DimInfer` argument calls per request | `ShapeDecode` term evaluations | `ShapeDecode` term units | `GenInfer` evaluations | Contract |
|---|---:|---:|---:|---:|---|
| Scene description | 5 | 15 | 63,133 | 0 | Pass (2/2) |
| Held self-knowledge | 1 | 3 | 17,392 | 0 | Pass (2/2) |
| Self-report action | 1 | 3 | 17,392 | 0 | Pass (2/2) |
| Unknown-word clarification | 1 | 3 | 17,392 | 0 | Pass (2/2) |
| Concern authoring | 1 | 3 | 17,392 | 0 | Fail (0/2) |

Every one of these five task classes reaches `DimInfer`/`ShapeDecode`; none
reaches generic `GenInfer`. This is a stronger task-diversity result than the
earlier two-prompt pilot, but the task set is still repository-authored and
cannot estimate natural traffic prevalence. It measures inference counters,
not uninstrumented latency or the frequency/cost of minting new structure.
Each fresh worker loaded 731 seeds and reported 11 optional seed failures; the
panel's existing boot gate requires positive loaded count and retains failures
for review, rather than requiring all optional seeds to load.

The independent v2 archive recorded six of ten task-contract passes, with
scene description failing both replicates. The current-source replay passes
that condition in both workers; the other four conditions preserve their
prior outcomes. Thus the source-linked task capability changed since that
capture. This is a paired descriptive comparison, not a causal attribution to
any individual source change.

Evidence: [protocol](LIVE_CONVERSATION_TASK_INFERENCE_COUNTERS_V1_PREREG_20261006.md),
[runner](../../../evaluation/substrate_capability/live_conversation_task_inference_counters_v1.py),
[lock](../../../evaluation/substrate_capability/live_conversation_task_inference_counters_v1_lock_20261006.json),
[capture](../../../evaluation/reports/live_conversation_task_inference_counters_v1_20261006.json),
[prior task-panel results](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V2_RESULTS_20261004.md),
and [prior analysis](../../../evaluation/reports/live_conversation_task_graph_harvest_v2_analysis_20261004.json).
