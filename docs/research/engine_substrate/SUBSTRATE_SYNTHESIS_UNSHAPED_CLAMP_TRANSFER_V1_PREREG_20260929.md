# Unshaped clamp synthesis transfer v1 — preregistration

**Status:** locked fresh-family panel. **Date:** 2026-09-29.

## Question

Can the normal program-synthesis route acquire and transfer simple scalar clamp functions using the broad default grammar when neither authored threshold operator-shape selector matches? This adds a task family using `Min`/`Max` composition after the greater/lower selector studies. It measures bounded task-specific synthesis, not induction of a new primitive or broad capability.

## Pilot disclosure

Two one-worker exploratory runs preceded this protocol. Both reached Rung 3 without an operator-shape selection, accepted Programs, and matched their manually checked holdouts: `clamp(x,0,5)` at 8,230 candidate tests and `clamp(x,-2,4)` at 6,663 tests. They are design pilots, not pooled evidence; the registered runner will freshly repeat both.

## Cases

Task A is `min(max(x,0),5)`, with training pairs `[-2→0, 0→0, 1→1, 4→4, 5→5, 7→5]` and disjoint holdout inputs `[-6,-4,-1,2,6,9]`.

Task B is `min(max(x,-2),4)`, with training pairs `[-5→-2, -2→-2, -1→-1, 1→1, 4→4, 7→4]` and disjoint holdout inputs `[-8,-3,0,2,6,9]`.

Requests are fixed as `write a function clamp_value between bounds 0 and 5` and `write a function clamp_value within limits negative two and 4`. Neither request contains the registered greater/lower trigger tokens. There are five fresh processes per task (10 total). Each process calls `ensure_program_synthesis`, `ingest_spec`, and ordinary `pump`; it does not set `ps_enum_ops`. Every accepted graph-reflected Program is run on all six holdout values through `ProgEval` and independently compared to the formula.

## Gates and measures

1. Lock and verify requests, data, explicit task order, code, source/seeds, native extension, and engine provenance; capture source/native stability for every worker.
2. Require exactly five unique workers per task, one header/footer, Rung 3 enumeration reached, no selected operator shape or explicit operator list, and terminal statuses.
3. Every accepted route has one reflected Program and six independently measured holdout results; report every false accept.
4. Report per-task accepted/exact-transfer rates, candidate tests, full `pump` wall/CPU times, peak RSS, gaps, and false accepts. The task-family transfer claim requires exact transfer in at least 4/5 workers per task.

No result from these two scalar clamp functions establishes broad default-grammar tractability, natural task prevalence, grammar learning, or scaling.
