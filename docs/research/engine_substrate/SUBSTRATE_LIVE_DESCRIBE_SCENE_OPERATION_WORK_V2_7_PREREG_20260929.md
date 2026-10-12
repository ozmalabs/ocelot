# Live describe-scene operation-work trace v2.7 preregistration

## Question

Measure native scheduler/deferred-queue work within the same production `describe_scene` route and paired concurrent fixture as v2.5, on one newly locked source snapshot. This repeats the v2.6 work-capture design after v2.6 was censored by detected source edits and an incompatible prior-source comparison.

## Frozen design

Capture three paired traced/untraced replicates in six fresh processes. Preserve the v2.5 fixture, per-request Goal ownership, shared Scene+Percept interface, concurrency schedule, task/lifecycle/reply oracle, whole-graph checks, and native access trace. For each traced request interval also snapshot `runtime_work_trace_snapshot()` rows `(operation_id, producer_rule_uid, kind, subject, work_units)`. Reset access and work traces at the start of each serialized request. Capture all rows before any subsequent request. Untraced intervals must produce empty access and work streams.

Do not use an earlier source revision as a semantic baseline. Bind the complete current source closure, native extension/build manifest, runner, analyzer, protocol, and native event source in one lock; require worker-start, worker-end, and post-run equality. Exact semantic graph/reply/lifecycle parity is required within each traced/untraced pair. Work counters are heterogeneous instrumented units, not cycles, elapsed time, or additive measures of one common cost.

## Gates

Require: three pairs/six distinct PIDs; no worker errors or live threads; source stability; schedule/task/lifecycle/reply gates; within-pair whole-graph and semantic parity; complete per-request access and work snapshots; zero access/work trace drops; untraced streams empty; process/request work totals reconcile; every observed work kind is defined in the locked native source. A failure censors the run; retain raw captures and do not pool partial results.

## Claim boundary

This measures only `note_work` call sites reached inside the serialized request schedule. UID 0 identifies work outside an active rule. No result is a complete operation cost, dependency graph, locality guarantee, or natural-task prevalence estimate. Host/Python work, full scheduler attribution outside instrumented sites, candidate-matching complexity, and safe scoped execution remain unmeasured.

## Reproduction

Use `PYTHONPATH=runners/dsl/python:.`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Create the source lock with `scripts/substrate_live_describe_scene_operation_work_v2_7.py --lock`, then run that script. The runner refuses to overwrite existing lock or output artifacts.
