# Work-trace overhead v1 preregistration

Date: 2026-09-28  
Status: paired live-route measurement; descriptive timing pilot.

## Question

What request-time and process-CPU overhead does all-scope operation-work tracing add on the locked `describe_scene` route when scale auditing is enabled in both arms?

## Design

Run three fresh-process paired blocks. Each block builds two fresh, identically seeded adapters with the same static/meter/mover fixture and request. One arm has work tracing disabled; the other enables work-only tracing across all graph scopes. Scale audit and per-rule audit stay enabled in both arms. Arm order alternates by block (`off,on`; `on,off`; `off,on`). Seed loading and scene setup are excluded from request timing. Measure `converse` wall time and process CPU time with monotonic/per-process clocks. Do not include build or boot time in the request metric.

## Registered checks and outputs

1. Three fresh worker processes, stable source/native lock, and complete paired arms.
2. Both arms return the exact expected reply and identical task-level observables (route, graph node/edge counts, goal count, outbound text).
3. Integer scale-audit work counters, excluding `_ns` timing fields, match within every pair.
4. Trace-off arms emit no work rows; trace-on arms emit nonempty rows with zero drops.
5. Report each arm's wall/CPU time, paired absolute and percentage deltas, median and range. Timing has no pass threshold and is not evidence of a general speedup or overhead rate.

## Claim boundary

This pilot estimates instrumentation overhead for all-scope work tracing on one authored dialogue request with scale auditing enabled. It does not estimate overhead with other audit settings, repeated/long-running tasks, natural workload mixes, or hardware profiles; task observables are not a full canonical graph-equivalence proof.
