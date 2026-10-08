# Coactivation population × Hebbian join order v1 preregistration

Date: 2026-10-01

## Question

Does the near-cubic CAN candidate-test growth track coactivation-relation population, and does starting the same Hebbian rule patterns from sparse coactivation edges reduce match work while preserving the graph result?

## Design

Use N={32,64,128} Concepts, 3 fresh-process replicates per cell, and five directed coactivation populations: Q=0, N, 4N, floor(N(N−1)/4), and N(N−1). Build pairs uniformly by directed cyclic offsets, then allocate one `Coactivation` node per pair. Concepts have state 1. The Microtheory has `can_tick=0`; coactivation `noted_tick`/`evidence_tick` are 1 so the two Hebbian rules cannot mutate. Disable every CAN rule except `can_native_hebbian_mint` and `can_native_hebbian_reweight`, preventing note/update rules from changing Q during measurement.

For each cell, run two in-memory rule variants from the exact same graph: baseline authored pattern order and sparse-first order that puts `coactivated_with`/`coactivation_of` clauses before `has_concept`. Load rules while the graph is empty so install-time edge-cardinality ties do not depend on Q; record the actually installed match clause order. Run production scoped closure with global/per-rule scale audit, capture `cand_tested`, `candidate_tests` by rule, enumeration/work counters and fixed-point state. The epoch guards make both branches read-only during closure; final graph signatures must remain exactly equal to each other and to the pre-run graph.

Panel: 3 sizes × 5 populations × 3 fresh process replicates = 45 workers, each paired across the two clause orders.

## Gates

- Complete all 45 unique cells with 45 PIDs and stable source/native fingerprints.
- Both named Hebbian rules are active; all other seed rules are inactive.
- Installed baseline begins with `has_concept`; sparse-first begins with `coactivated_with` for both rules.
- `can_tick` guards prevent writes; fixed point is immediate and final graph digests match the pre-run digest and each other.
- Per-rule candidate-test totals equal global `cand_tested` in every arm.
- Report candidate tests/work by N, Q, rule, and order. No wall-time speed threshold or asymptotic claim is preregistered.

## Limits

This is an isolated production-rule matcher workload with synthetic uniformly distributed coactivation records, not full CAN learning closure. It identifies the effect of relation population and match order in these two rules; it does not validate arbitrary rewrites, natural coactivation distributions, or a universal complexity class.
