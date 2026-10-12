# Live conversation task inference counters v1

Status: preregistered task-diverse production-route counter capture.

## Question

Across the existing five-condition live conversation panel, which task routes
execute `DimInfer`, `GenInfer`, `ShapeDecode`, or `TransformDecode`, and what
native term-unit counts do those calls record?

## Frozen task set

Reuse the exact five authored task conditions and two-replicate schedule from
the source-locked live conversation task-graph harvest v2: scene description,
unknown-word clarification, held self-knowledge, concern authoring, and self-
report. Each worker boots a fresh full-seed `WorldAdapter` and sends exactly
one prompt through `WorldAdapter.converse`. The source v2 task contract is
retained and evaluated for each run. The panel is deliberately task-diverse,
but its prompts are repository-authored and are not sampled from user traffic.

## Measurements and gates

Reset native scale counters at the `WorldAdapter.converse` boundary, enable
global audit counting during that request, then record counters and restore
the disabled state. Preserve the existing task wall/CPU fields as contextual
instrumented observations only; do not use them as production latency.
Capture per request: `dim_infer_arg_calls`, `term_eval:DimInfer`,
`term_eval:GenInfer`, `term_eval:ShapeDecode`,
`term_eval:TransformDecode`, `term_unit:ShapeDecode`, and
`term_unit:TransformDecode`.

Require ten workers, two workers per condition, source stability, one counter
observation per request, positive loaded-seed count (matching the base panel's
boot contract; optional seed failures are retained descriptively), and repeat
parity in task-contract outcome and task reply. The task-contract pass count is descriptive and must
match between the paired workers. Counter values are not required to be equal
across task classes. This experiment measures reachability/frequency only; it
does not establish a population rate, causal contribution to task success, or
un-instrumented latency.

## Source integrity and command

The lock covers this runner and protocol, the live task-graph harvest v2
runner/protocol/lock/analyzer/analysis/capture, its runtime input manifest,
the current native engine, Cargo metadata, and source-provenance helper. The
independent v2 analyzer's `task_oracle` is used for task outcomes. Build the current
default engine, then run:

```sh
python3 evaluation/substrate_capability/live_conversation_task_inference_counters_v1.py --lock
python3 evaluation/substrate_capability/live_conversation_task_inference_counters_v1.py
```

The compact result is written to
`evaluation/reports/live_conversation_task_inference_counters_v1_20261006.json`.
