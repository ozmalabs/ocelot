# Held-topic trace semantic-parity replay v1.1 preregistration

Date: 2026-09-28  
Status: preregistered after a development discrepancy probe; confirmatory paired replay not yet run.

## Motivation and scope

The v1 instrumented run was captured against a locked source snapshot that was subsequently changed in `substrate/world_adapter.py`. A current-worktree one-process development probe now returns different held-topic outcomes. A five-arm instrumentation probe on that newer source showed equal semantic signatures across baseline, access trace, per-rule counters, all-scope work trace, and combined tracing, but it shared one process and is development evidence only. V1 results remain historical evidence for the exact locked snapshot and must not be represented as current capability status.

This replay tests whether the combined trace instrumentation preserves the fixed held-topic workload on the current source closure. Each of three fresh processes boots two independent agents and runs the same teaching/query schedule once with the baseline timer and once with the combined instrumentation. Arm order is counterbalanced (baseline-first for replicates 0 and 2; trace-first for replicate 1). The task order and prompts remain fixed. The replay records full worker states and operation traces for the trace arm.

## Semantic parity oracle

For each paired worker, require exact equality between baseline and trace arms for:

- teaching topic and returned answer;
- every prompt, final reply, comprehension dispatch, selected message route/surface, associated Goal attributes, held answers, grounding evidence, production receipts, and request statuses;
- complete operational frame member IDs, internal/boundary edge lists and counts, node/type summaries, and induced-width upper bound.

Require the same paired semantic signature across the three workers. Separately apply the existing fixed capability oracle to both arms. The oracle result is a workload result; a failed case is reported without weakening the signature check.

## Trace-integrity gates

For each measured trace-arm operation require: zero dropped access/work rows; weighted access-count conservation; all observed RuleUIDs resolved; no observed static-resource mismatch; valid work rows; exact reconciliation of all-scope rows with scope and process-global scheduler/deferred counters; complete operation-kind markers; and independent reconstruction of every task-frame cut and attribute schema. Lock the full Python/seed source closure, native extension, native build manifest, protocol, amendment, driver, analyzer, trace helper, and baseline runner before and after every process. Also content-hash the complete repository `data/` tree before and after the three-process replay: the previous isolated snapshot omitted this 3.9 GB runtime corpus and produced different boot graphs and task outcomes despite a matching Python/seed closure. Run from the actual workspace so all other local runtime assets are available; record working directory, environment, and commit provenance.

## Claim boundary

Passing establishes semantic transparency only for this fixed workload, source/native build, and enabled instrumentation. It does not establish zero overhead, trace completeness, natural-task prevalence, task-frame discovery, a cheap cut, or partitioned fixed-point correctness. Any semantic mismatch blocks use of traced outcomes as capability evidence until isolated. The v1.1 run does not claim to repair conversation behavior.
