# Live conversation task inference counters v1.1 results

**Result: ten fresh workers pass source, boot, per-request capture, and paired
task-repeat gates.** This recapture keeps the complete native global counter
map at each `WorldAdapter.converse` boundary, not only the selected fields.

All five authored task conditions invoke `DimInfer`/`ShapeDecode`. Scene
description records five `dim_infer_arg_calls`, 10 `term_eval:DimInfer`, 15
`term_eval:ShapeDecode`, and 63,133 shape-decode term units per request. Each
other condition records one `dim_infer_arg_calls`, two `DimInfer` term
evaluations, three `ShapeDecode` term evaluations, and 17,392 shape-decode
term units. The higher-volume scene task is consistent across both replicates.

Across every task and replicate, the full counter map records zero
`gen_infer_requests`, zero `gen_infer_kernel_calls`, and zero matrix attempts.
`term_eval:MetaShapeMint` is omitted from all ten maps; this is an explicit zero
because the source emits only nonzero per-variant term rows while emitting
`term_evals_total` unconditionally, and that total is positive in every
observation. Thus no generic `GenInfer` search or `MetaShapeMint` evaluation
occurred on these routes. The task contracts pass 8/10: scene
description, held self-knowledge, self-report, and unknown-word clarification
pass twice; concern authoring fails twice. Each worker loaded 731 seeds and
recorded 11 optional seed failures, matching the existing panel's permissive
boot contract.

This directly distinguishes frequent `DimInfer` evaluation on the selected
panel from generic GenInfer search and rung-four mint execution, which were
not reached there. It does not establish their frequency on naturally sampled
tasks, other APIs, background activity, or long-lived processes. Counters are
instrumented operation counts, not wall-time or causal-attribution results.
The task set remains repository-authored and selected.

See [protocol](LIVE_CONVERSATION_TASK_INFERENCE_COUNTERS_V1_1_PREREG_20261006.md),
[runner](../../../evaluation/substrate_capability/live_conversation_task_inference_counters_v1_1.py),
[lock](../../../evaluation/substrate_capability/live_conversation_task_inference_counters_v1_1_lock_20261006.json),
[full-counter capture](../../../evaluation/reports/live_conversation_task_inference_counters_v1_1_20261006.json),
[`term_rows` counter semantics](../../../runners/dsl/src/scale_audit.rs),
and [v1 task-diverse results](LIVE_CONVERSATION_TASK_INFERENCE_COUNTERS_V1_RESULTS_20261006.md).
