# ProblemShape recurrence index paired timing preregistration

**Status:** exploratory confirmatory timing follow-up; semantic and operation-count protocol is unchanged.

## Question

For the largest already-tested recurrent-residual cell (N=8), does the candidate residual-event plus key-support index change observation-to-receipt wall time relative to the unmodified baseline when measured in randomized fresh-process pairs?

## Arms and fixed inputs

- Baseline: locked `substrate_problem_shape_population_scale.py` worker with N=8, recurrent-residual, dynamic codebook.
- Candidate: `substrate_problem_shape_recurrence_index.py` worker with N=8, recurrent-residual.
- Three pairs, each arm in a distinct process; order randomized per pair from fixed Python RNG seed `20260925` before execution.
- Same current native binary and workload seeds. The baseline implementation, candidate runner, seeds, and native binary are hash-locked before any paired worker starts.
- Primary outcome: sum of per-observation `wall_time_ns` for baseline versus `treatment_observation_wall_ns` for candidate. Both intervals end immediately after closure and receipt, with instrumentation snapshot readback outside timing.

## Required checks and analysis

Each process must pass its arm's semantic/fixed-point checks. Process IDs must all be distinct. Report every pair's raw times, candidate/baseline ratio, paired median ratio, and candidate/index maintenance and rule-work counters. No exclusion, trimming, or replacement is permitted. If any worker fails semantics, retain it and report paired timing as inconclusive. Three pairs are still exploratory; no general performance claim or natural-task claim follows.

## Limits

This is one N=8 workload family and three pairs. It does not test persistence, concurrent ingestion, rollback, other rule families, or overall substrate scalability. It only improves repeatability for this prototype comparison.
