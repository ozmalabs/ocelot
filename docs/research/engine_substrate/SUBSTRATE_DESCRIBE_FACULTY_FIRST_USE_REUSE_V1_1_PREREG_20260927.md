# Describe faculty first use and reuse v1.1 preregistration (2026-09-27)

## Amendment rationale

The v1 pilot gate incorrectly treated every native rule added during a request as describe-faculty construction. The source route separately calls `_ensure_describe` before request processing and then `_conceptualize_scene_lines` later. The v1 pilot observed 18 rules during explicit `_ensure_describe`, six additional conceptualizer rules during the first request, and no additional rules during the second request. v1.1 preserves the same arms and worker schedule while separating those phases. The pilot remains reported as a failed-gate run; these observations motivate the corrected confirmation gate.

## Question and design

Measure boot, first-use faculty construction, first and second request wall/CPU, current RSS, peak RSS, rule-count deltas, and task lifecycle in three fresh workers per arm. Alternate arms in a six-worker schedule. The **lazy** arm lets request one invoke `_ensure_describe`; the **prebuilt** arm invokes `_ensure_describe` after scene attachment and before request timing. Both then run two sequential identical scene-description requests. No access tracing, scale audit, or graph readback is enabled in measured phases. Hash runtime and protocol inputs before and after every worker.

## Confirmatory gates

- Six unique fresh processes, three per arm; no lock drift.
- All workers load the full seed profile, complete two identical expected replies, and recover one resolved Goal per request with `selection`, `execution`, and `action_result` events.
- Lazy: first request adds 24 rules (18 faculty plus six conceptualizer in this source lock); second request adds zero.
- Prebuilt: explicit `_ensure_describe` adds 18 rules before request timing; first request adds six conceptualizer rules; second request adds zero.
- Report every replicate and per-arm median/range for boot, explicit faculty construction, both requests, current RSS, and peak RSS. Failed workers remain in the report and invalidate aggregate capability claims.

## Interpretation limits

This confirms timing decomposition and cached reuse only on the locked scene route. The prebuilt and lazy arms pay equivalent setup work at different points; this is not a natural-task frequency estimate, rule-necessity ablation, transfer test, or scaling curve. Rule-count checks classify phase deltas by schedule and known source behavior; they do not prove causal necessity.
