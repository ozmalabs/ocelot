# Work-trace overhead v3 preregistration

Date: 2026-09-28  
Status: corrected 2×2 instrumentation pilot after the V2 scheduler-hook audit.

## Method correction

The V2 timing capture showed only 106 work units in trace-only arms versus 229,763 in audit-and-trace arms. Source inspection found that the scheduler slot hook was called only when scale auditing started its timing interval. V2 therefore did not exercise complete scheduler-work tracing with the audit off, and its trace-only overhead contrast is not accepted as a complete-trace estimate.

The native path now records scheduler slot/probe work when either scale auditing or work tracing is enabled. Trace-only mode performs the same counted fixed-point probe loop as audit-on mode, but does not start a scheduler timer or update scale-audit counters. The factorial arms and timing procedure otherwise remain as specified in V2.

## Question and arms

Measure scheduler/deferred work-trace overhead on the live `describe_scene` request, separately with scale audit off and on:

| Arm | Scale audit | Per-rule audit | Work trace |
|---|---:|---:|---:|
| `baseline` | off | off | off |
| `audit_only` | on | on | off |
| `trace_only` | off | off | on, all graph scopes |
| `audit_and_trace` | on | on | on, all graph scopes |

Run three fresh-process blocks with registered rotated orders. Exclude full-corpus setup from request wall/process-CPU timers.

## Gates

1. Three fresh workers and stable source/native locks.
2. All four arms match on expected reply and task-level observables.
3. Integer scale counters match between `audit_only` and `audit_and_trace`.
4. The five scheduler work totals in `trace_only` match the `audit_only` scale-counter control exactly. This verifies equal counted scheduler work across the audit-off/on trace arms.
5. Tracing-disabled arms have no rows; trace-enabled arms have rows; all drops are zero.
6. Report raw per-arm request timings and factorial contrasts. There is no timing threshold; three blocks are a pilot and do not support a general overhead bound.

## Claim boundary

This measures one authored route with exact scheduler work parity across audit settings. Deferred queue work is compared by outcome observables and existing counter parity between audit arms; the trace-only arm has no independent queue counter oracle when scale audit is off. The result does not generalize across tasks, sizes, or hardware, and does not include memory or energy.
