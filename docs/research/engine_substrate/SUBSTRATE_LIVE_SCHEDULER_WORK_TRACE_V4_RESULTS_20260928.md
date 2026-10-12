# Live scheduler-work trace v4 results

Date: 2026-09-28

## Result

The preregistered three-worker all-scope capture passes all 17 independent checks. Every worker returns the expected `describe_scene` reply; source/native inputs are stable; there are no dropped work rows. Each capture includes six graph scopes and 67 typed operations: 22 `run_rules` calls and 45 `apply_rule_once` calls. This route invokes no `apply_rule_batch` operation.

Every graph-scope work row reconciles with its scoped scheduler/deferred counters, and the sum across scopes matches every process-global counter in the preregistered scheduler and five-queue families. The framebuffer residual from v3 is assigned to two graph scopes, with 11 and 5 drain batches respectively.

| Work measure | All-scope trace and global counter |
|---|---:|
| Scheduler passes | 39 |
| External-poll rule slots | 87,187 |
| Fixed-point probe slots | 1,174 |
| Dirty-vector slots | 87,187 |
| Selected rules | 54,093 |
| `fb_samples` drain batches | 16 |
| Other queue-family enqueue/drain units | 0 |

The two scopes active in v3's `run_rules` trace account for 37 scheduler passes. The additional 2 passes (8 slots, 2 probes, 8 selections) occur in another graph scope and are now included. Operation-kind markers show the one-shot application calls that were missing from the earlier capture and own the 16 framebuffer drains.

## Claim boundary and next gate

This closes scheduler/deferred counter attribution across all graph scopes and the three instrumented operation kinds for one authored live route. It does not cover arbitrary host operations, matcher candidate tests, Term evaluations, callback internals, or establish frame locality, natural workload prevalence, or scaling. Next measure tracing overhead under paired enabled/disabled arms, extend typed operation coverage to other rule-driving entrypoints, and connect complete operation dependencies to the frame-locality contract.

## Reproduction

Build and extract the source-locked release wheel, then run:

```sh
SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_live_scheduler_work_trace_v4.py --lock

SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_live_scheduler_work_trace_v4.py

python3 scripts/analyze_live_scheduler_work_trace_v4.py
```

Artifacts: [preregistration](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V4_PREREG_20260928.md), [runner](../../../scripts/substrate_live_scheduler_work_trace_v4.py), [independent analyzer](../../../scripts/analyze_live_scheduler_work_trace_v4.py), [source/native lock](../../../evaluation/substrate_capability/live_scheduler_work_trace_v4_lock_20260928.json), [raw capture](../../../evaluation/reports/live_scheduler_work_trace_v4_20260928.json), and [analysis](../../../evaluation/reports/live_scheduler_work_trace_v4_analysis_20260928.json). Earlier scope-limited captures remain preserved in [v1](SUBSTRATE_SCHEDULER_WORK_TRACE_V1_RESULTS_20260928.md), [v2](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V2_RESULTS_20260928.md), and [v3](SUBSTRATE_LIVE_SCHEDULER_WORK_TRACE_V3_RESULTS_20260928.md).
