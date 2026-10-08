# Live scheduler-work trace v1 preregistration

Date: 2026-09-28  
Status: focused operation-attribution capture on one live dialogue route.

## Question and workload

Does the operation-scoped work trace account for scheduler activity across the full `describe_scene` request, and do its scheduler and deferred-queue totals reconcile with the native scale-audit counters?

Each fresh worker loads the full seed corpus, attaches the same static/meter/mover scene, and submits `describe what you see` through `WorldAdapter.converse`. The runner enables the work trace and scale audit before the request, then captures all work rows, counters, the reply, and a semantic graph digest. Three fresh processes run one request each. Inputs and native binary are source-locked before and after.

## Registered checks

1. Three distinct worker PIDs complete with stable source/native hashes.
2. Each worker returns the expected fixed-scene response and the same semantic graph digest.
3. Work rows use the registered five-field schema `(operation_id, producer_rule_uid, kind, subject, units)`; no rows are dropped; each row has a nonzero operation ID and positive work units.
4. Aggregate work units for scheduler passes, external polls, fixed-point probes, dirty-vector slots, and selected rules exactly equal corresponding scale-audit totals.
5. For every deferred queue family, work-trace enqueue, drain-batch, and drained-item totals exactly equal the corresponding scale-audit counters, including zero-valued families.
6. Operation IDs and per-operation work totals are retained to show the number and distribution of instrumented `run_rules` calls.

## Claim boundary

This measures operation attribution and counter conservation on one authored live route. It does not establish trace recall outside instrumented hooks, queue prevalence in natural tasks, operation-to-frame completeness, learned locality, scheduler scaling, or instrumentation overhead. The full-corpus boot cost is setup and is not included in request timing claims; this study makes no timing claim.

## Reproduction

Build and extract the native wheel from the locked source. Set `SUBSTRATE_NATIVE_PACKAGE` to its extracted package directory and `SUBSTRATE_NATIVE_WHEEL` to the wheel. Run the new runner with `--lock`, then without arguments, followed by the independent analyzer.
