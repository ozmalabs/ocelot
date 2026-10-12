# Join multiplicity clause attribution v1.1 preregistration

Date: 2026-09-26

## Question

Which match-edge positions account for the candidate-test growth observed in join-multiplicity v1, and how do candidate work and deferred queue work change at larger multiplicities and under a different pattern order?

## Design

Use `R={1,8}` writer/target pairs and `M={1,4,16,32,64}` successful two-edge paths per writer. Compare `trigger_left_right` authored order (`trigger,left,right,game`) against `trigger_right_left` authored order (`trigger,right,left,game`). Both authored orders keep the one-edge trigger first, preventing the wide first-edge parallel matcher from bypassing per-rule context on later clauses. Three fresh-process replications per cell yield 60 workers. Each writer queues one rule edit and framebuffer sample per successful binding, then deletes its trigger. Audit-off and audit-on twins are independently constructed. A new opt-in native counter reports candidate tests by native rule index and zero-based **installed** match-edge position. The runner also reads back `export_rules()` after installation and records the actual edge-type order; do not infer clause labels from authoring order because `add_rule` applies a cost-based reorder.

## Gates

- Stable engine/source/protocol/runner/analyzer lock across all workers.
- Plain/audit whole-graph and report parity; fixed point, no budget overshoot.
- Exactly `R` target output edges, `4R` framebuffer grid cells, and no trigger edges.
- Each queue family enqueues/drains exactly `R×M` items in one batch.
- Each writer rule is attributed exactly `M` enqueues per queue family.
- The sum of per-clause candidate tests for each writer equals that writer's independent per-rule `candidate_tests` total.
- Both join orders produce identical final graph state for equal `(R,M)`.
- Exported installed edge order is captured for both audit arms and checked against the engine's count-based reorder behavior; per-clause counts are attributed to installed edge type.

Candidate tests are matching work, not time. Scheduler planning time remains a distinct interval and excludes matching, effects, and queue drains. Whole-closure timing is not claimed by this protocol.

## Limits

The regular topology and repeated queue effects are synthetic. Only two join orders, two rule counts, and this four-literal pattern are represented. Clause attribution depends on the current-rule context; this fixture's first candidate set has one edge, so the parallel batch matcher should remain inactive. The analyzer must check clause/per-rule conservation rather than assume instrumentation coverage.
