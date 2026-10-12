# Common-ground ordinary seed/task cost v1 preregistration

Date: 2026-09-29, before confirmatory capture.

## Question and claim boundary

Measure the current ordinary seed-loading and default native closure route for
the frozen ten-event common-ground task, without test-harness rule replacement
and without scale counters enabled. Separate fresh adapter construction,
`load_seeds_into`, chat/state setup, event ingestion, per-event closure,
terminal fixed-point verification, and complete task wall/CPU time. This is a
single authored task family, not a natural-task estimate, general latency
claim, or commodity-scale throughput result.

## Frozen workload and execution

Use `phase3_common_ground_stress.v1` in fixture order and the current
`conversation_discourse_state` seed through `WorldAdapter(seeds=())` followed
by the ordinary `load_seeds_into` API. Do not remove/re-add rules, reorder
clauses, add decoys, or enable global/per-rule/per-clause counters. Add only
the six fixture-supplied `event for_goal goal` links required by the existing
identity oracle, at the same event indices as the prior explicit arm. Their
source is benchmark input, not production event ingestion.

Run ten fresh processes with identical inputs and distinct PIDs. At each of
the ten fixture events, time ordinary `inner.run_rules(100_000)` separately
from event construction. After the final event, run one separately timed
terminal no-change probe; verify that it reports zero progress and leaves the
complete graph digest unchanged. Record loaded seed IDs, lifecycle rule
readbacks, progress counts, task paths, common-ground claims, graph size,
process CPU/RSS, and per-stage wall/CPU timings. Time the worker's Python
module imports separately from the task stages so fresh-worker import cost is
not silently assigned to rule closure.

## Gates

- Ten unique fresh PIDs; all worker source/native fingerprints equal the
  pre-run lock and remain unchanged after capture.
- The registered seed closure loads and exactly three active discourse
  lifecycle rules are present; no rule is removed, re-authored, or replaced.
- All ten event closures plus the terminal probe use the ordinary
  `run_rules` API, not `run_rules_report`; all terminal probes report zero
  progress and preserve complete graph identity.
- Every worker passes the two-goal identity and common-ground oracles; all ten
  workers have identical terminal graph digests.
- Scale counters were never enabled by the runner. Report medians, ranges,
  and all per-worker stage values; no outlier deletion or speed threshold.

Report each stage separately. Do not add them to prior audit-enabled or
rule-reinstallation timing results as though they were paired measurements.
The next gate remains an independently authored task topology and a separate
ordinary end-to-end production route.

## Development pilot disclosure

One excluded worker was run before locking to validate ordinary seed loading,
all ten task oracles, the no-change terminal probe, and disabled counters. It
passed those semantic checks and loaded `conversation`,
`conversation_discourse_state`, and `relations`. Its measured worker span was
about 75 ms while seed load plus construction and closures accounted for about
6 ms, revealing a large import/setup residual. This prompted the explicit
module-import timer above. The pilot is not part of the locked ten-worker
capture and its timings are not confirmatory evidence.
