# Scheduler work-trace overhead scale v2 preregistration

Date: 2026-09-28  
Status: warmed repeated fixed-point factorial after the v1 timing-resolution diagnostic.

## Motivation and design correction

V1 passed counter/semantic checks, but its single closure calls took tens to hundreds of microseconds. Three pairs produced timing deltas comparable to timer and host noise, with unstable percentages. V2 retains the same 8/32/128-rule fixtures and factorial arms but warms each graph to its exact fixed point, then times 256 repeated fixed-point `run_rules_report` calls per arm. Setup and warmup are outside the timer. This increases the measured interval while preserving the scheduler path whose instrumentation is under study.

## Arms

For each size, compare `baseline` (audit off, trace off), `audit_only`, `trace_only`, and `audit_and_trace`. Three fresh processes use the registered rotated arm orders. Work tracing uses all-scope operation capture. The five trace-only scheduler totals must match audit-only scale counters exactly.

## Gates

1. Three fresh workers and complete size×arm coverage; source/native hashes stable before/after each worker.
2. Warmup derives all N expected edges; all 256 timed calls in every arm return fixed-point status; final graph digests agree across arms within size.
3. Scale-audit integer scheduler counters match between audit-only and audit-and-trace arms.
4. Trace-only scheduler work totals match audit-only scheduler counters exactly at each size.
5. Work rows are absent with tracing off, present with tracing on, and have zero drops.
6. Report total batch and per-call timing contrasts with pair ranges. Three pairs remain a pilot with no threshold or broad speed claim.

## Claim boundary

This improves timing resolution for steady-state positive-graph scheduler closure. It does not measure full mutation-to-fixpoint cost, matcher-dense scaling, live route orchestration, queues, memory/energy, or a natural workload distribution. Relative overhead at N=8 may remain noisy even with repetition.
