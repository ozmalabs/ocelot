# Scheduler/deferred work trace v1 preregistration

Date: 2026-09-28  
Status: preregistration for one fixed synthetic operational fixture; not a general scheduler-cost experiment.

## Question

Can the new operation-work trace expose scheduler and deferred-queue work under a stable operation ID, while matching the existing independent scale-audit counters and preserving the expected fixed point?

## Fixture and workload

Each fresh worker builds one graph with one writer and one target rule. The writer queues one `SetRuleClause` edit and one 2×2 framebuffer sample, then removes its trigger edge. The between-pass drains apply both queued effects; the target rule then emits one expected `seen` edge. A local 4×4 BGRA frame in `/dev/shm` supplies deterministic framebuffer input. Each worker runs one ordinary monolithic `run_rules_report` call with access tracing and scale auditing enabled.

Three independent worker processes run the same fixture once each. This is a focused mechanism verification, not a factorial, latency study, natural-prevalence sample, or test-suite run. A development one-worker smoke was run before this protocol was written; it is excluded from confirmatory evidence.

## Registered gates

1. Three fresh PIDs complete; source and loaded native hashes match the source lock before and after each worker.
2. Each run reaches fixed point with exactly two progress steps and three completed passes; the trigger is absent, the target edge is present, and four expected grid cells exist.
3. The work trace has zero dropped rows, one operation ID, and identical aggregate work rows across workers.
4. Scheduler work rows exactly equal scale-audit counters for passes, external-poll slots, fixed-point-probe slots, dirty-vector slots, and selected rules.
5. Deferred work rows exactly equal enqueue, drain-batch, and drained-item counters for both `rule_edits` and `fb_samples`. Enqueues have a nonzero producer UID; drains have UID 0 and are grouped by queue-family subject code.
6. Rule-scoped access-trace rows have zero drops. Their weighted event totals and graph-effect rows are recorded separately; they are not merged with operation-work units.
7. All workers have the same canonical graph digest, rule report, scheduler/queue counters, and operation-work rows. Drain timing is retained as descriptive data and excluded from exact equality.

## Claim limits

Passing establishes scoped attribution and counter parity for this one scheduler call and two deferred families. It does not cover the other queue families, scoped scheduling, mutation requeues, concurrent calls, all scheduler paths, or general trace recall. Work outside `run_rules` has no operation ID in this experiment. No speedup or runtime overhead claim is registered.

## Reproduction

Build the native wheel from the locked source, extract it to a package directory, and set `SUBSTRATE_NATIVE_PACKAGE` to that directory. Then run `scripts/substrate_scheduler_work_trace_v1.py --lock`, followed by the runner without arguments. The runner writes the raw workers capture; the independent analyzer writes the machine analysis.
