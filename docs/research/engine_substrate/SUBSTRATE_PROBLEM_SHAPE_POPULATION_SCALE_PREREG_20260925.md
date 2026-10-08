# ProblemShape observation-population and frozen-codebook sweep preregistration

**Status:** confirmatory mechanism envelope for the authored ProblemShape pathway; each cell uses a fresh process. It is not a natural-task prevalence study.

## Question

How do per-observation ProblemShape candidate/term work and observe latency change with the number and mix of observations, and what cost/state change is associated with enabling recurrence-driven minting?

## Factorial design

- Population sizes: `N=2,4,8` observations per worker.
- Task mixes: `recognition` (alternate real deduction and Bigville CAN exact goals); `recurrent_residual` (repeated real decomposition goals whose common structure is not in the initial codebook).
- Codebook conditions: `dynamic` (normal rules); `frozen` (tombstone only the `ps_mint` rule before observations; all other rules and inputs remain the same).
- One fresh subprocess per size × mix × codebook cell: 12 workers total, no within-process reuse across cells.
- All workers use full seed boot, identical fixed-order task generation within each factor cell, native audit-on per-rule counters, and an exact expected status/mint oracle.

## Measures and acceptance

Record per-observation initial/final status, codebook size, mint count, node/edge changes, ProblemShape-rule candidate pairs and term evaluations, whole-engine counters, wall/CPU time, setup cost, peak RSS, build and seed hashes. Recognition tasks must all recognize with zero mints. For recurrence tasks, dynamic mode must produce exactly one mint for `N≥2`, re-decode the first residual, and recognize all later same-shape observations; frozen mode must mint zero and leave all observations residual. Both modes must have exact expected final status and keep engine status `fixed_point`.

## Analysis rules

Show per-observation and cumulative attributed work against `N`, separated by task mix and mint condition. Timing is descriptive because this is one worker per cell with instrumentation enabled. Compare candidate counts as the primary work measure; do not pool whole-engine counts as if they belonged to ProblemShape. A difference between dynamic and frozen conditions is attributable to rule deactivation only within this controlled synthetic setup; it does not establish a field prevalence or general learning advantage.

## Limits

The two task families are small and project-authored; decomposition goals share one deliberately recurrent shape. The frozen condition removes one rule through the public native `remove_rule` path and is an ablation, not a production mode. No false-mint precision, independent task-family transfer, or natural residual-rate estimate follows.

## Reproduction

Run `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_problem_shape_population_scale.py --output evaluation/reports/substrate_problem_shape_population_scale_20260925.json` after verifying the native build is current.

## Amendment v1.1 — verify worker isolation in the raw data

Record each worker PID and require 12 distinct PIDs in the aggregate result. This makes the preregistered fresh-process condition directly auditable from the report; no task, size, or acceptance criterion changes.
