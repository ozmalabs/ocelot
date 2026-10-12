# Finite-key join work attribution — preregistration (2026-09-26)

**Status: locked before counter capture.** This adds direct engine work counters
to the existing locked join-arity/topology matrix. It is a separate audit-on
measurement and will not replace or be timed against the ordinary closure runs.

## Question

How many candidate pairs/tests, rule enumerations, leaf visits, and Term
evaluations does the native matcher perform for each previously measured
`(topology,N,q)` closure, and how do those counts relate to the independent
positive path-binding count?

## Fixed method

- Reuse the exact 42 topology/size/arity inputs, rule body, match-binding
  enumerator, and expected final graph from
  `SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_PREREG_20260926.md`.
- Three fresh substrates per cell, in a deterministic shuffled schedule, in
  each of two fresh processes (126 closures per process).
- Build graph/rule with scale audit disabled. Immediately before closure, reset
  all global/per-rule counters, enable global and per-rule audit, run native
  closure, collect both snapshots, then disable both audit modes.
- Record integer counters only; discard audit-on wall times from complexity
  comparisons. Keep the original uninstrumented timings as the separate cost
  evidence.
- Require exact final graph hash, binding/terminal counts, fixed point, budget
  and bound checks; verify documented counter conservation and equality between
  global and summed per-rule metrics. Compare all counter records exactly across
  the two processes.

## Counters and boundary

Capture `cand_enum` split by scan/local/hinted and first/repeat, `cand_tested`,
`where_evals`, `leaf_visits`, `rule_enumerations`, `term_evals_total`,
`term_units_total`, and graph/effect writes. Also preserve the full snapshot so
zero and newly relevant counters remain inspectable. These are native
instrumented site counts, not CPU instructions; Term units are site-specific.
The independent enumerated path-binding count is a workload descriptor, not
assumed equal to any native counter. This fixed positive schema does not measure
arbitrary plans, natural workloads, or instrumentation overhead.
