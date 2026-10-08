# Scheduler work-trace overhead scale v2 results

**Date:** 2026-09-28  
**Status:** all preregistered integrity and semantic gates passed; timing is a three-block pilot.

## Protocol and scope

Three fresh processes each ran a four-arm instrumentation factorial on synthetic positive rule fixtures with 8, 32, and 128 rules. Each graph was warmed to its fixed point before timing, then each arm timed 256 repeated `run_rules_report` fixed-point calls. Arms were baseline, scale audit only, work trace only, and both. Setup and warmup were outside the timed interval; arm order was rotated. Source and native hashes were locked and checked before and after every worker.

## Gate results

The independent analyzer passed all preregistered gates: three distinct processes; complete 3×3×4 workload grid; stable source/native locks; all warmups at fixed point; all 256 calls per arm at fixed point; exactly N trigger and N derived edges with matching final graph digests across arms; audit counter equality between audit-only and combined arms; trace-only scheduler-work totals equal audit-only scheduler counters for all five scheduler measures; trace absent when disabled, present when enabled, and zero dropped work rows. See the [preregistration](SUBSTRATE_SCHEDULER_TRACE_OVERHEAD_SCALE_V2_PREREG_20260928.md), [runner](../../../scripts/substrate_scheduler_trace_overhead_scale_v2.py), [analyzer](../../../scripts/analyze_substrate_scheduler_trace_overhead_scale_v2.py), [raw capture](../../../evaluation/reports/scheduler_trace_overhead_scale_v2_20260928.json), [analysis](../../../evaluation/reports/scheduler_trace_overhead_scale_v2_analysis_20260928.json), and [source/native lock](../../../evaluation/substrate_capability/scheduler_trace_overhead_scale_v2_lock_20260928.json).

## Timing observations

Across the three process blocks, the median trace-only wall-time differences versus baseline were 106,110 ns (415 ns/call) at 8 rules, 127,791 ns (499 ns/call) at 32 rules, and 49,770 ns (194 ns/call) at 128 rules. The corresponding block ranges were 82,951–186,022 ns, −15,650–338,723 ns, and 19,020–111,270 ns. Percent differences were correspondingly unstable: medians 12.0%, 15.0%, and 5.3%, with ranges crossing zero at 32 rules. CPU differences show the same broad pattern and process-to-process spread.

These measurements support only a rough sub-microsecond-per-call trace cost for this warmed, positive, no-new-work scheduler path on this host/build. They do not estimate tracing overhead for mutation-to-fixpoint closure, matcher-heavy rules, live orchestration, large graphs, deferred queues, or memory/energy. Three blocks are insufficient for a general overhead bound; the wide ranges and several sign changes require more repetitions and longer timed batches before quoting a stable percentage.

## Next measurement

Preserve this as a passing instrumentation control. To estimate useful operational overhead, preregister a source-stable multi-size benchmark that times mutation plus closure, increases repeated batches enough to dominate timer noise, and covers both sparse and matcher-dense rule families. Keep audit and trace as separate factorial factors, retain exact graph/report parity, and report per-call and per-unit-work costs with process-block ranges. Then repeat on at least one live route without relying on the route whose Python adapter source changed during prior captures.
