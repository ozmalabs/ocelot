# Live describe-scene operation-work trace v2.6 preregistration

## Question

How much native scheduler/deferred-queue work occurs inside the request intervals measured by v2.5, and how much of it is attributed to a rule versus scheduler work outside a rule? This adds the separately exposed `runtime_work_trace_snapshot` to the same production route and concurrent fixture.

## Frozen design

Use the v2.5 worker fixture and paired traced/untraced schedule, with the same semantic task oracle, Goal-derived ownership policy, shared Scene+Percept interface, and exact whole-graph parity checks. In each traced request interval, retain both concrete access rows and `runtime_work_trace_snapshot()` rows `(operation_id, producer_rule_uid, kind, subject, work_units)` before the next interval resets the recorder. In untraced arms, require both streams to remain empty. Report work by kind, operation, and rule UID, with UID 0 distinguished as work outside a rule. Do not sum overlapping work categories as wall-clock time.

The six-process design can take roughly three minutes because the held schedule pauses request A while B serializes. Keep that behavior unchanged; it is part of the existing fixture, not representative throughput.

## Gates and claim boundary

Require three paired replicates/six PIDs, source stability, task/lifecycle/reply gates, exact graph/semantic parity, complete per-request work snapshots, zero work-trace drops, and count reconciliation between per-request snapshots and process-level work totals. Compare v2.6 traced-arm projections with the immutable v2.5 traced workers by replicate for reply, lifecycle, graph digest, and task boundary parity.

The result measures only instrumented native operation work covered by existing `note_work` call sites. It does not measure total CPU operations, Python/host work, complete matcher complexity, or a safe frame cut. Treat all work counters as attributable units, not cycles or elapsed time. If any v2.5 parity or source gate fails, retain but censor the run.

## Reproduction

Use `PYTHONPATH=runners/dsl/python:.`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Create the lock with `scripts/substrate_live_describe_scene_operation_work_v2_6.py --lock`, then run the script. The runner refuses to overwrite existing outputs.
