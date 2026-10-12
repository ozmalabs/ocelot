# Scheduler/deferred work trace v1 results

Date: 2026-09-28

## Result

The preregistered three-worker replay passes all 11 independent analyzer checks. Each fresh process reaches the same fixed point in two progress steps and three passes, writes the expected `seen` edge, and produces four framebuffer grid cells. Canonical graph digests, work-event rows, scale counters, and access-trace summaries agree across all workers; each worker has a distinct PID, one operation ID, and zero work/access trace drops.

The new `runtime_work_trace_snapshot()` returns operation ID, producer rule UID, work kind, optional queue-family subject, and work units, separately from graph-access rows. It matches the existing scale audit exactly for this fixture:

| Work class | Trace units | Scale-audit units |
|---|---:|---:|
| Scheduler passes | 3 | 3 |
| External-poll rule slots | 6 | 6 |
| Fixed-point probe slots | 4 | 4 |
| Dirty-vector slots | 4 | 4 |
| Selected rules | 4 | 4 |
| `rule_edits` enqueue / drain batch / drained items | 1 / 1 / 1 | 1 / 1 / 1 |
| `fb_samples` enqueue / drain batch / drained items | 1 / 1 / 1 | 1 / 1 / 1 |

Queue subjects are family codes 1 (`rule_edits`) and 3 (`fb_samples`). Enqueue rows carry the nonzero producer RuleUID; drain rows carry UID 0 and the family code. Scheduler rows also use UID 0 and share the `run_rules` operation ID. Timing counters vary across workers and remain separate: scheduler-plan time is 610–710 ns, rule-edit drain 25,290–26,140 ns, and framebuffer drain 12,470–14,730 ns. These tiny fixture timings are descriptive only; this study makes no overhead or speedup claim.

## Claim boundary and next gate

This confirms that scheduler and two deferred queue families can be scoped to one `run_rules` operation and reconciled with existing counters. It does not establish general scheduler trace recall, the other three deferred families, scoped scheduling, concurrent execution, out-of-run host work, or task-frame boundaries. Next extend the capture to the remaining queue families and a second live task route, then compare the work trace under trace-on/off arms to quantify instrumentation overhead.

## Reproduction

The local editable environment's `maturin develop --release` path failed because `runners/dsl/.venv` lacks its Python executable. The captured binary was built with `maturin build --release`, extracted from the resulting abi3 wheel, and selected through `SUBSTRATE_NATIVE_PACKAGE`; the lock records the native binary and wheel hashes plus the Rust source fingerprint. Rebuild and extract a wheel, then run:

```sh
SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_scheduler_work_trace_v1.py --lock

SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_scheduler_work_trace_v1.py

python3 scripts/analyze_substrate_scheduler_work_trace_v1.py
```

Artifacts: [preregistration](SUBSTRATE_SCHEDULER_WORK_TRACE_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_scheduler_work_trace_v1.py), [independent analyzer](../../../scripts/analyze_substrate_scheduler_work_trace_v1.py), [source/native lock](../../../evaluation/substrate_capability/scheduler_work_trace_v1_lock_20260928.json), [raw workers](../../../evaluation/reports/substrate_scheduler_work_trace_v1_20260928.json), and [analysis](../../../evaluation/reports/substrate_scheduler_work_trace_v1_analysis_20260928.json).
