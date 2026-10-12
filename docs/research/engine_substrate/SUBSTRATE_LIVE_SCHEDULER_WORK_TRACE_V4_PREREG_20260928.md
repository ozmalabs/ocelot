# Live scheduler-work trace v4 preregistration

Date: 2026-09-28  
Status: all-scope replay including one-shot rule-application operations.

## Motivation

V3 captured all active `run_rules` scopes and reconciled each scope's trace with scoped counters, but 16 global framebuffer drain batches remained outside those operations. Source inspection located a second valid drain path: `apply_rule_once` and `apply_rule_batch` drain pending framebuffer samples after the single application, outside the fixpoint loop.

## Change and workload

Add explicit work-operation IDs and kind markers for `run_rules` (1), `apply_rule_once` (2), and `apply_rule_batch` (3). Apply-rule entrypoints receive instrumentation only; rule matching, effects, and queue drains are unchanged. Repeat the same locked three-worker full-corpus `describe_scene` request with work-only all-scope tracing.

## Registered checks

1. Three fresh workers complete with stable source/native locks and expected reply.
2. Every operation-work row has valid scope/operation IDs and positive units; no rows are dropped; each operation has exactly one supported kind marker.
3. Every graph-scope scheduler/deferred counter matches the corresponding traced work units.
4. Per-scope totals across every observed graph sum exactly to process-global scheduler/deferred counters. Residuals fail this gate and remain explicit.
5. Operation-kind counts, operation-indexed work totals, scope-normalized counter profiles, and residual vectors reproduce across workers. Raw pointer scope IDs are not compared across processes.

## Claim boundary

Passing assigns scheduler/deferred work from the named operation kinds to graph scopes on one authored route. It does not include candidate matching, Term evaluation, host callbacks, unrelated graph operations, or prove task-frame locality or scaling. The v3 capture and its 16-batch residual remain archived unchanged.
