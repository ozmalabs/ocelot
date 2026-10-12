# Work-trace overhead v1 results

Date: 2026-09-28

## Result

The preregistered three-process paired pilot passes all seven analyzer checks. The trace-off and trace-on arms matched exactly within every pair on the expected reply, route, graph node/edge counts, goal count, outbound text, and all non-timing scale-audit counters. Trace-off arms recorded zero operation-work rows; trace-on arms recorded work with zero dropped rows. Source/native hashes were stable.

Scale auditing and per-rule auditing were enabled in both arms; only all-scope operation-work tracing differed. Full-corpus boot and scene setup were outside the request timer. The measured trace-on minus trace-off differences were:

| Measure | Median paired delta | Range across 3 pairs |
|---|---:|---:|
| Request wall time | +508 ms (+3.66%) | +380 to +600 ms (+2.75% to +4.29%) |
| Process CPU time | +508 ms (+3.67%) | +376 to +629 ms (+2.73% to +4.52%) |

All three pairs showed positive measured overhead. This is a descriptive result for one authored request; three pairs do not provide a stable estimate across tasks, task sizes, or machines.

## Claim boundary and next gate

This estimates the added cost of all-scope scheduler/deferred work tracing on one `describe_scene` route while scale audits are already enabled. It does not estimate the cost with auditing disabled, isolate per-counter or mutex costs, cover longer/repeated workloads, or measure energy and memory. Next run trace-only and audit-off controls over multiple workloads and sizes, including a large synthetic graph, while checking semantic and integer-counter parity.

## Reproduction

Use the locked release wheel and run:

```sh
SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_work_trace_overhead_v1.py --lock

SUBSTRATE_NATIVE_PACKAGE=/path/to/extracted/substrate_rs \
SUBSTRATE_NATIVE_WHEEL=/path/to/substrate_rs-...whl \
python3 scripts/substrate_work_trace_overhead_v1.py

python3 scripts/analyze_work_trace_overhead_v1.py
```

Artifacts: [preregistration](SUBSTRATE_WORK_TRACE_OVERHEAD_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_work_trace_overhead_v1.py), [independent analyzer](../../../scripts/analyze_work_trace_overhead_v1.py), [source/native lock](../../../evaluation/substrate_capability/work_trace_overhead_v1_lock_20260928.json), [raw pairs](../../../evaluation/reports/work_trace_overhead_v1_20260928.json), and [analysis](../../../evaluation/reports/work_trace_overhead_v1_analysis_20260928.json).
