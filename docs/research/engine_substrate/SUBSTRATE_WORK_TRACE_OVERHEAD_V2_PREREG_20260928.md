# Work-trace overhead v2 preregistration

Date: 2026-09-28  
Status: paired 2×2 instrumentation pilot on the live dialogue route.

## Question

How much request-time overhead comes from operation-work tracing when scale auditing is off, and how does that compare with the trace effect when scale/per-rule audits are on?

## Factorial design

Each of three fresh-process blocks builds four separate adapters from the same full seed corpus and scene fixture. The measured arms are:

| Arm | Scale audit | Per-rule audit | Work trace |
|---|---:|---:|---:|
| `baseline` | off | off | off |
| `audit_only` | on | on | off |
| `trace_only` | off | off | on, all graph scopes |
| `audit_and_trace` | on | on | on, all graph scopes |

Arm order rotates by block to reduce fixed order effects. Boot and setup stay outside request timers. Wall and process CPU time are measured only around `WorldAdapter.converse`. The primary trace overhead contrasts are `trace_only − baseline` and `audit_and_trace − audit_only`; `audit_only − baseline` estimates the audit cost in the no-trace arm. Their difference is reported as an interaction diagnostic.

## Registered checks

1. Three fresh workers, all four arms in each, stable source/native hashes, and the registered arm orders.
2. Expected reply and task-level observables (route, graph node/edge counts, goals, outbound text) match within each block.
3. Integer scale-audit counters match between the two audit-enabled arms.
4. Trace-disabled arms have no work rows; trace-enabled arms have work rows; all arms have zero dropped rows.
5. Report raw arm times and paired factorial contrasts with median/range. No timing threshold or generalized performance conclusion is registered.

## Claim boundary

This isolates instrumentation contrasts on one authored live task. It does not estimate overhead across task families, sizes, memory behavior, or hardware, and task observables do not prove full canonical graph equivalence. Trace-enabled mode includes work aggregation and operation-kind markers; default-off static checks are common to all arms.
