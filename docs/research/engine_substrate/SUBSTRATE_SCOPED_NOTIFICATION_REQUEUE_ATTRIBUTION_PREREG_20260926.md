# Scoped notification and requeue attribution preregistration (2026-09-26)

## Question

Which scheduler costs explain the tree/star event-settlement slowdown after local candidate seeding: repeated owner notifications, queue-suppressed duplicate notifications, self-requeues, queue depth, or repeated no-progress frame turns?

## Design

Replay the existing chain, binary-tree, and star propagation fixtures at 8, 16, 32, and 64 frames, with five paired repetitions and the same on/off state transitions, four rules, graph construction, local matcher, native build, and cap as `SUBSTRATE_SCOPED_LOCAL_CANDIDATE_V1_1_AMENDMENT_20260926.md`. Do not alter Rust code or graph semantics. Keep full-closure arm and exact projection/parity gates as references. Attribute each event arm's settlement loop per turn and per owner.

For each turn record current owner, progress steps, number of reported affected-owner entries, unique affected owners, self notifications, notifications suppressed because that owner is already queued, successful enqueues, queue depth before/after and maximum depth, and before/after deltas for native candidate, term, and scoped matcher-path counters. Aggregate frame turn counts, no-progress turns, total duplicate suppressions, self requeues, and owner notification multiplicity. Raw per-turn records are authoritative; independent analysis recomputes every aggregate.

## Gates

1. Inputs and native/source fingerprints match the current checkout at capture time.
2. Paired arms have identical fixture topology and cardinality; full arms reach fixed point.
3. Event arms settle within cap, with no deferred effects, and match full projections exactly in both transition phases.
4. Every event owner notification is attributable to an observed write turn, and raw per-turn counters sum to the captured phase totals.
5. Aggregates recomputed independently from raw turn records exactly match runner summaries.
6. Repeat medians and ranges are reported; wall time remains descriptive and does not itself identify causality.

## Interpretation limits

These authored synthetic graphs do not establish natural-task queue behavior or frame locality. Attribution identifies scheduler costs in this harness; it does not show that batching/coalescing is semantically safe. A scheduler optimization requires a separate intervention with exact ordering, notification, omission, termination, and event/full parity gates.

## Outputs

Raw capture: `evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926.json`. Independent analysis: same basename with `_analysis.json`. Runner and analyzer: `scripts/substrate_scoped_notification_requeue_attribution_v1.py` and `scripts/analyze_substrate_scoped_notification_requeue_attribution_v1.py`.
