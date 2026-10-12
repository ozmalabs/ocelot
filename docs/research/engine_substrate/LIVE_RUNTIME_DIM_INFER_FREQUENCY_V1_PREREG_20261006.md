# Live-runtime DimInfer frequency pilot v1

Status: preregistered re-analysis of an existing source-locked runtime capture.
This is a descriptive pilot, not a representative task-prevalence estimate.

## Question

Do the two prompt routes in the locked live-runtime closure capture invoke
native `DimInfer`/`ShapeDecode`, and what per-prompt native term counters are
observed when the audit instrumentation is enabled?

## Population and method

Use only audit-on runs from
`live_runtime_closure_counters_v1_6_20261004.json.gz`, which has three
replicates and two prompt routes (`report your organisation`; `describe who
you are`). Require the existing independent v1.6 analysis to pass, raw capture
integrity/source-stability gates to pass, and exactly one observation of each
prompt in each replicate. Extract `dim_infer_arg_calls`,
`term_eval:DimInfer`, `term_eval:GenInfer`, `term_eval:ShapeDecode`,
`term_eval:TransformDecode`, `term_unit:ShapeDecode`, and
`term_unit:TransformDecode`. Missing counters count as zero only when the
counter schema is present for that observation.

The unit is a prompt execution in this capture. The two prompt strings repeat
across replicates and are not independent natural tasks. Do not extrapolate
the counts or frequency to a broader user/task distribution, or treat these
instrumented counters as wall-time measurements.

## Integrity

The runner locks itself, this protocol, the existing v1.6 raw capture, its
source lock, and its passing independent analysis. It emits a compact JSON
summary without copying prompt event payloads. Expected sample: six prompt
executions (three replicates × two routes).
