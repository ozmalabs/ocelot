# Vision settlement native work attribution preregistration

Date: 2026-09-25. Follow-up to the locked global/scoped scaling run.

## Question and design

Attribute candidate and Term work to `st_settle` versus `st_settle_root_scoped_benchmark` at 4/16/64/256 SUnits. Use the same seed 4101, resized-retina rule, matched deterministic afferents, and 1,024 application budget as the scaling benchmark. Build a fresh world per variant/size, enable the existing native `scale_audit` and per-rule counters only for the measured run, and record rule-index/name mappings, global counters, per-rule counters, progress, and final activation. Compare each audited run's progress and activations to seed 4101's uninstrumented record. Audited timings are diagnostic and excluded from timing estimates.

Require exact progress and activation parity with the uninstrumented run. Require summed per-rule `candidate_tests`, `term_evaluations`, and `term_units` to equal corresponding global `cand_tested`, `term_evals_total`, and `term_units_total`. Report all counters, including zeros, and distinguish generic matcher work from the aggregate Term work. Do not infer asymptotic behavior from four sizes.

## Limits

This attributes one rule pair on a synthetic single-sheet family; instrumentation is opt-in and adds overhead. It does not establish natural-workload frequency, multi-sheet behavior, full fixed-point cost, or production frame-local execution.
