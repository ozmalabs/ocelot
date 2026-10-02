# Native work attribution for scaled solver alternatives v1.2 preregistration

Date: 2026-10-01

## Question

Which native work counters scale with N and topology in the 32/128/256 Concept CAN solver-alternative workload, and does candidate testing, Term evaluation, rule enumeration, scheduler polling, or deferred queues account for the sharp closure-time rise observed in v1.1?

## Design

Repeat the v1.1 18-worker source/native-locked panel and four perturbations per worker. Keep the same path/banded2 graph construction, candidate order, and reusable/eager semantics. Immediately before each branch's `scoped_settle`, reset and enable global and per-rule scale audit; collect global counters, per-rule counters, and rule metadata, then disable audit before fixed-point verification and readout. Keep the v1.1 uninstrumented timing report as the timing reference. V1.2's instrumented wall times are not used as performance evidence because per-rule audit adds work.

## Gates

- Complete 18 workers / 72 branch pairs with stable locks and the same graph/solver outputs as v1.1.
- Capture nonzero `cand_tested` and `rule_enumerations` for all instrumented solves. This path uses scoped closure, so global-scheduler counters are not presumed applicable; record scoped match-source counters separately.
- Report candidate tests, enumeration source/locality and repeats, Term evaluation/units, rule enumeration, where evaluation, scoped match-source counters, and any deferred queue counters by N, topology, and backend. Report global scheduler counters explicitly as zero/not used when that is what the capture records.
- Retain per-rule records and require summed per-rule candidate-test counts to equal global `cand_tested` for every branch; report mismatches without coercion.

## Limits

Counters are operation units, not cycles or time; per-rule auditing changes runtime cost. Work is one native CAN solver and two authored sparse topologies. This attributes the tested panel only and does not establish a complexity bound, natural workload distribution, solver quality, or CoW speedup.
