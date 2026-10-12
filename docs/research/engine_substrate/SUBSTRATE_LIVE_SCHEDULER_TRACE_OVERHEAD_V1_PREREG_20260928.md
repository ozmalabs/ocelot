# Live scheduler-work trace overhead v1 preregistration

Date: 2026-09-28  
Status: preregistered paired instrumentation-cost diagnostic.

## Question

On the current full-seed `describe what you see` route, how much measured conversation time and semantic output change when enabling (a) global and per-rule scale counters and then (b) all-scope scheduler/deferred work tracing on top of those counters?

## Design

Use three fresh-process arms per replicate, with fixed rotate order across three replicates:

1. `baseline`: scale audit, per-rule audit, and work trace disabled;
2. `counters`: global and per-rule scale audit enabled; work trace disabled;
3. `counters_work_trace`: the same audits plus all-scope work trace enabled.

Each arm loads the full seed corpus, attaches the same three-item scene, and performs exactly one `describe what you see` instruction from Alice. Timer scope is the `WorldAdapter.converse` call only. Boot time, whole-process peak RSS, scheduler/deferred counters, work rows, reply, graph size, and a semantic graph digest are recorded separately. The semantic digest omits only `SystemModel.ts` and `SystemModel.runtime_s`.

Replicate arm orders are baseline/counters/trace, counters/trace/baseline, and trace/baseline/counters. There are nine fresh processes. All source, native, runner, protocol, and analyzer inputs are locked before capture and checked before/after each worker and after the run.

## Preregistered checks and interpretation

- Every process returns the exact expected reply and matching normalized semantic graph digest/node/edge counts across all arms and replicates.
- Counter and trace arms must have nonzero measured instrumentation records; baseline must have zero scale/work counters and zero trace rows.
- `counters` and `counters_work_trace` must have equal scale-counter vectors; the latter's work rows must reconcile to those counters by graph scope and globally.
- Report per-replicate paired ratios: counters/baseline and counters+trace/counters. Report raw observations and medians; do not infer a general overhead factor from three pairs.
- Timings are descriptive host measurements and may be noisy; semantic mismatch or source drift censors the affected comparison.

## Claim boundary

This isolates instrumentation overhead for one authored route and current source snapshot. It does not estimate overhead on other tasks, native matcher/Term audit modes beyond the stated flags, instrumentation interaction under concurrency, or end-to-end frame-locality cost. Exact reply/graph parity does not establish complete trace recall.
