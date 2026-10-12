# Context-scale replay v1.1 cost-capture amendment

Date: 2026-09-29, before the v1.1 timing capture.

The v1 capture measures exact native candidate work and installed order but
does not measure installation cost. This amendment adds a fresh-process
replication of the same frozen 0/8/32 decoy × 24 authored-order × three-repeat
grid. It wraps only the Python call boundary around `inner.add_rule` and
`inner.remove_rule` and records wall-clock and process-CPU nanoseconds for the
three lifecycle-rule removals and three corresponding additions in each
worker. The target rule's add call includes its existing native relation-count
reordering. The call-boundary timer excludes JSON export, analysis, and worker
startup. Decoy contexts, fixtures, task sequence, rule effects, and success
criteria are unchanged from v1.

The runner also retains v1's ten audit-enabled closure timings and matcher
work. Those times remain instrumented diagnostics; they are not uninstrumented
latency. No instrumentation-on/off timing comparison is added, so this
amendment does not authorize a speed or amortized-runtime claim. The analysis
will report target `add_rule`, all lifecycle add/remove totals, and audit-on
closure time separately, including per-context distributions and exact
semantic parity checks. Source, native artifact, preregistration, amendment,
runner, analyzer, base runner, seed, fixture, and relevant native sources are
locked before capture.
