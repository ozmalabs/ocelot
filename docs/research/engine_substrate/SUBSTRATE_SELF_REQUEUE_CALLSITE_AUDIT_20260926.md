# Self-requeue optimization call-site audit (2026-09-26)

## Finding

The guarded self-requeue result does not currently transfer to an in-tree production event scheduler. `run_rules_scoped_delta_report` has no callers under `domains/`, `substrate/`, or `worlds/`; the only Python occurrence in those/package roots is its wrapper definition in [`ext.py`](../../../runners/dsl/python/substrate_rs/ext.py). The scoped report queue is currently implemented in measurement runners such as [`substrate_scoped_notification_requeue_attribution_v1.py`](../../../scripts/substrate_scoped_notification_requeue_attribution_v1.py), not in a production domain path.

The production-facing [`can_native_orchestration.scoped_settle`](../../../domains/can_native_orchestration.py) calls `run_rules_scoped(max_steps, False, mt)` once for one Microtheory and returns its progress count. Its callers in [`self_improvement_loop.py`](../../../domains/self_improvement_loop.py), [`insight_detection.py`](../../../domains/insight_detection.py), and [`solver_dispatch.py`](../../../domains/solver_dispatch.py) consume that one-owner fixpoint; they do not drain owner notifications or implement a cross-frame queue. Other matches in domain files are comments/docstrings. The native scoped closure therefore has no self-notification queue action to suppress in these production paths.

## Consequence

Do not add a guard to the engine based only on the synthetic event-queue speedup. The guarded policy remains an experimentally supported scheduler-harness optimization. An opt-in engine integration would first require a real caller with a queue over multiple Microtheories and an explicit contract for when local settlement is saturated. That call site must also expose membership/boundary invalidation and a route to compare with monolithic closure. Until such a caller exists, prioritize the remaining tractability programme rather than creating a production queue solely to apply the optimization.

## Reproducible source audit

Run from repository root:

```sh
rg -n "run_rules_scoped_delta_report" domains substrate worlds runners/dsl/python --glob '*.py'
rg -n "run_rules_scoped\\(" domains --glob '*.py'
```

This is a static call-site inventory, not runtime reachability or a complete audit of dynamically invoked native methods.
