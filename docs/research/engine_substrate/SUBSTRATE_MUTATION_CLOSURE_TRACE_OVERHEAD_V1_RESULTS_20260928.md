# Mutation-to-fixpoint trace overhead v1 results

**Date:** 2026-09-28  
**Status:** amended semantic/work gates pass; timing estimate remains inconclusive.

## Run and gates

Three fresh source/native-locked worker processes covered 8/32/128 rules, sparse and matcher-dense families, and baseline/audit-only/trace-only/combined arms. Each arm timed 32 independently built fixtures; construction was excluded, while the trigger insertion and full native `run_rules_report` closure were included. Total timed closures: 2,304.

All analysis checks pass. Every call reached fixed point. Sparse fixtures produced one progress step and one derived edge; dense fixtures produced one progress step and eight derived edges. Graph digests and reports matched across arms. Audit-only and combined integer counters matched. Trace-only scheduler work matched audit counters, tracing had no drops, and the candidate-work oracle passed: 32 candidate tests per sparse arm cell and 2,304 (=32×(8²+8)) per dense arm cell. This confirms that the fixtures exercised the intended sparse and two-clause join paths.

Evidence: [preregistration](SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_PREREG_20260928.md), [protocol amendment](SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_mutation_closure_trace_overhead_v1.py), [analyzer](../../../scripts/analyze_substrate_mutation_closure_trace_overhead_v1.py), [raw capture](../../../evaluation/reports/mutation_closure_trace_overhead_v1_20260928.json), [independent analysis](../../../evaluation/reports/mutation_closure_trace_overhead_v1_analysis_20260928.json), and [source/native lock](../../../evaluation/substrate_capability/mutation_closure_trace_overhead_v1_lock_20260928.json).

## Timing

Median trace-only wall-time deltas per closure, with the min–max across three process blocks, were:

| Family | Rules | Median ns/call | Block range ns/call |
|---|---:|---:|---:|
| Sparse | 8 | 2,606 | 2,239 to 2,976 |
| Sparse | 32 | −5,892 | −6,888 to −786 |
| Sparse | 128 | 4,903 | −51 to 10,405 |
| Matcher-dense | 8 | −572 | −23,427 to 29,186 |
| Matcher-dense | 32 | −24,733 | −112,145 to 64,357 |
| Matcher-dense | 128 | 178,717 | −927,604 to 765,105 |

Negative deltas and the wide block ranges show that this design still does not resolve instrumentation cost reliably. The results do not support claiming either a fixed nanosecond cost or a stable percentage overhead. The measured loop includes Python-to-native mutation and closure calls; process scheduling and runtime noise remain comparable to or larger than the trace effect in these three-block cells.

## Interpretation and next gate

This is a successful work-attribution and semantic-parity result for two authored workload families, not an overhead bound. The dense join is demonstrably more matcher-intensive by candidate count, while the trace-only latency contrast remains unidentifiable at this replication level. To estimate overhead, use more independent process blocks and larger per-block timed batches, collect host scheduling/context-switch data, and report paired log-ratios with uncertainty. Keep sparse and matcher-dense results separate. The earlier eight-fixture captures are retained as [failed-oracle pilot](../../../evaluation/reports/mutation_closure_trace_overhead_v1_failed_oracle_pilot_20260928.json) with [analysis](../../../evaluation/reports/mutation_closure_trace_overhead_v1_failed_oracle_pilot_analysis_20260928.json), and [short-batch pilot](../../../evaluation/reports/mutation_closure_trace_overhead_v1_short_batch_pilot_20260928.json) with [analysis](../../../evaluation/reports/mutation_closure_trace_overhead_v1_short_batch_pilot_analysis_20260928.json); they are not confirmatory evidence.
