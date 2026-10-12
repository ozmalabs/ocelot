# Monolithic scheduler work v1 results (2026-09-26)

## Question

Does the ordinary monolithic scheduler's planning work match its explicit slot counts on sparse, no-match rule sets, and does this expose how it scales with rule count?

## Method

The preregistered sweep used 1, 8, 32, and 128 identical active rules, with three fresh-process replications at each size. Each worker made a first closure call with all rules initially dirty and a second warm fixed-point call. Plain and audit-enabled arms were paired within each worker. The capture locked the Rust sources, runner, analyzer, preregistration, build manifest, native extension, and commit.

## Results

All 12 workers used identical locked inputs before and after execution. The analyzer passed 220/220 checks, including exact plain/audit status and graph parity, fixed-point behavior, and integer scheduler work.

On the first call with `R` rules, observed counts were exactly: one pass, `R` external-poll slots, one fixed-point probe slot, `R` dirty-vector slots, `R` selected rules, and `R` rule enumerations. On the warm call, counts were exactly: one pass, `R` external-poll slots, `R` fixed-point probe slots, zero dirty-vector slots, zero selected rules, and zero rule enumerations. Thus the measured scheduler planning work is linear in rule count on this workload, as the loops imply.

The audit-on planning timer was descriptive: at 128 rules, first-call samples were 9.95, 9.71, and 12.86 microseconds; warm-call samples were 0.21, 0.20, and 0.22 microseconds. This is a tiny synthetic workload and the measured interval excludes queue drains and rule execution. It is not a commodity-scale throughput estimate.

## Interpretation and limits

This establishes exact slot accounting and the expected linear scan on one sparse no-match workload. It does not establish useful wall-clock scale, behavior on positive/dense matches, scoped scheduling cost, external-gated polling prevalence, frame locality, or natural-task work. It also does not support a treewidth or separator claim: no frames were constructed or inferred. The next scheduler gate should measure dirty density and positive work while preserving the same paired semantic oracle, then integrate with runtime-derived rule-access/dependency data. The broader frame-partition question remains open.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_MONOLITHIC_SCHEDULER_WORK_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_monolithic_scheduler_work_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_monolithic_scheduler_work_v1.py)
- [Raw worker report](../../../evaluation/reports/substrate_monolithic_scheduler_work_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_monolithic_scheduler_work_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_monolithic_scheduler_work_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/monolithic_scheduler_work_v1_lock_20260926.json)
