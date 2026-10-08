# Scheduler work-trace overhead scale v1 preregistration

Date: 2026-09-28  
Status: source-stable native 2×2 overhead panel after live-route source drift.

## Question

How does work-only operation tracing affect request wall and process-CPU time across scheduler sizes, with scale auditing off versus on?

## Fixture and arms

Each fresh worker builds positive one-edge workloads with 8, 32, and 128 rules. Every rule matches one uniquely typed trigger edge and adds its corresponding derived edge; the fixture expects one fixed point with exactly N trigger and N derived edges. Setup is excluded from the timed `run_rules_report` call.

For each size, run four arms in rotated order:

| Arm | Scale/per-rule audit | All-scope work trace |
|---|---:|---:|
| `baseline` | off | off |
| `audit_only` | on | off |
| `trace_only` | off | on |
| `audit_and_trace` | on | on |

Three fresh worker processes provide one paired factorial block per size each. This is an overhead pilot, not a statistically powered performance study.

## Registered checks

1. Three fresh PIDs and stable source/native hashes before and after every worker.
2. Every cell reaches fixed point with exact expected trigger/derived edge counts; canonical graph digests match across all arms within size.
3. Audit-on integer scheduler counters match between `audit_only` and `audit_and_trace`.
4. Trace-only scheduler work totals exactly match the audit-only scheduler counter control at every size.
5. Trace-off arms have no work rows; trace-on arms have work rows and zero drops.
6. Report per-size paired trace effects with audit off/on, audit-only effect, and raw per-arm wall/CPU times. No sign or magnitude threshold is registered.

## Claim boundary

This measures instrumented scheduler overhead on three controlled positive-matching graph sizes. It excludes live task orchestration, queue families, callbacks, memory/energy, and natural workload distributions. Results do not establish a commodity-CPU envelope or whole-architecture overhead.
