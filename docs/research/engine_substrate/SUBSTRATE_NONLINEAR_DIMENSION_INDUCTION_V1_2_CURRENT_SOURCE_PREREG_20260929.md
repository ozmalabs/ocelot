# Nonlinear dimension induction current-source replication v1.2

**Lock date:** 2026-09-29, before execution. **Question:** does the registered full-seed induction/transfer contrast reproduce under the current Rust source and native extension?

## Relationship to v1.1

This is a source-refresh replication of the v1.1 task, not a new nonlinear learner or an expanded hypothesis class. The frozen v1.1 source lock differs from the current checkout in `runners/dsl/src/term.rs` and `runners/dsl/python/substrate_rs/_native.build.json`. The current engine provenance check reports `source_match=own`, so the loaded native extension is built from this checkout's Rust source. The new lock will include the current runner, analyzer, this protocol, the same seed/source inputs, generated cases, and the native extension hash. No v1.1 results are changed or pooled.

## Locked task and arms

Repeat the exact v1.1 60-case design: linear `T(x,y)=(x+y,2y)` positive control, quadratic shear `T(x,y)=(x+y²,y)`, and piecewise shear `T(x,y)=(x+max(y−1,0),y)`; six training and six separately identified transfer relations; production induction enabled versus frozen/no induction; ten fresh substrates per family and arm; and the original deterministic schedule seed. Keep the registered point sets, relation representation, generated identities, and transfer scoring unchanged. Each transfer target is exposed only after the training observation and acquisition state are recorded.

The replication's purpose is to refresh source attribution and check whether the previous measured boundary remains under the current build. Any design or source changes during capture invalidate admission. The runner must record source/native input hashes before and after all workers, and the independent analyzer must verify the actual loaded/current native hash and all source hashes against the frozen lock.

## Outcomes and admission

Retain the v1.1 classifications: induced and independently transferred; induced but invalid; residual/refusal; held structure only; and false explanation. Require all 60 family/replicate/arm cells, fresh-substrate semantics, exact lock and pre/post source/native agreement, the exact linear positive control, no linear fit to the nonlinear schedules in the registered search envelope, independent matrix application on transfer rows, and repeatable semantic outcomes. Report latency distributions by family and arm, but interpret them as one current-host/source replication and compare with v1.1 descriptively.

A failed current-source gate is inconclusive, not evidence of capability loss. Passing repeats the bounded source-specific result only; it does not establish an open-ended nonlinear learner, natural-task frequency, or an asymptotic complexity guarantee.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_nonlinear_dimension_induction_v1_2.py --lock
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_nonlinear_dimension_induction_v1_2.py
python3 scripts/analyze_substrate_nonlinear_dimension_induction_v1_2.py
```
