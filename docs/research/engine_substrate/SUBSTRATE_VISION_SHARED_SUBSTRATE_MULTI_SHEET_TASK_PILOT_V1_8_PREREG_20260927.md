# Shared-substrate closure-pass state trace v1.8 preregistration

## Question
When do `oo_sunit_activate`, `oo_sunit_rate`, `st_latch_aff`, `st_settle`, and `st_commit` change per-unit state, and what exact orbit causes `repeated_graph_state` in v1.7?

## Locked inputs and fixture
Use the v1.7 prepared graph checkpoint, v1.7 raw report/source lock, seed 20260934, same Retina/SUnit identities, and both root-scoped and global rule variants. Restore the exact prepared graph before every condition. Apply the same four stimuli (both blank, B-only exact grating, A-only exact grating, both exact gratings), each with one +10 Retina step. Capture both sheets' `act`, `theta`, `rate`, `act_step`, `rate_step`, and SUnit `bursting` after each complete substrate pass, along with progress report, whole-graph exact digest, and selected rule order. Manually detect repeated states using exact serialized graph digests; stop at fixed point, exact recurrence, or 512 passes.

## Slicing preflight
For root-scoped B-only and global both-gratings, independently compare a single full `run_rules_report(200000, true)` closure with repeated one-pass slices using `run_rules_report(1, false)`. Require equal exact terminal graph digests, equal fixed-point versus cycle classification, and equal total progress steps and pass count. If any check fails, retain diagnostics but do not interpret the pass-sliced traces as the committed closure trajectory.

## Analysis and claims
Capture integrity, slicing equivalence, and semantic findings are separate. Report every pass trace and the exact cycle start/period. Report which fields change on a pass relative to their stamps and to the rule order. A mismatch between final `act` and `rate=max(act-theta,0)` is an observed timing distinction, not automatically a defect; determine whether `rate` is pre-settle by ordering evidence. This one adapted graph cannot establish general behavior, but it will set a valid measurement contract for later scope/task/scale panels.
