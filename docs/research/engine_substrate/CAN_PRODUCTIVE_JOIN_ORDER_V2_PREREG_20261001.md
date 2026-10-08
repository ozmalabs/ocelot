# Productive CAN join-order validation v2 preregistration

Date: 2026-10-01

## Question

Does the minimum-prefix-work order from the CAN mixed-degree panel preserve productive outcomes when the production CAN Hebbian rules run with their real guards and effects? Compare authored, sparse-first, and the exact measured best sequence.

## Design

Reuse the v1 productive fixture, source and size/population/repetition grid: N={32,64,128}, Q={0,N,4N,floor(N(N−1)/4),N(N−1)}, three fresh processes per cell. All rules are installed before graph population, so their match order is determined by authored sequence under tied empty-graph cardinalities. Construct each arm independently and verify the actual installed sequence after installation.

The three measured runtime orders are:

- default: normal installation heuristic with the original authored clause list; on the empty graph this installs as `has_concept(a), has_concept(b), coactivation_of(coact,b), coactivated_with(a,coact)` because equal-cost tie selection uses swap-removal;
- sparse-first: `coactivated_with(a,coact), coactivation_of(coact,b), has_concept(a), has_concept(b)`;
- measured best: `has_concept(a), coactivated_with(a,coact), coactivation_of(coact,b), has_concept(b)`.

Use the same real `where` clauses and productive effects in both production rules. The measured-best arm uses the new explicit order-preserving install API, while the default arm remains on the ordinary heuristic path. Preserve the v1 workload construction, including the supplied eligible coactivation ledger and half of the pairs pre-seeded for reweighting. Run full native closure, recording per-rule/global work, progress, elapsed time, canonical graph digest, per-pair effects, and one terminal fixed-point probe. Repeat each arm without instrumentation for semantic parity.

## Gates

- 45 unique worker cells and stable source/input lock.
- Exactly the two target rules are active and all three expected installed sequences are exact.
- Every arm reaches a terminal fixed point below the 100,000-step cap.
- Per-pair causal/evidence oracle and graph-size bounds pass for every arm.
- Canonical final graph facts match across all three orders for each fixture.
- Instrumented and uninstrumented runs match in progress and canonical graph facts.
- Target per-rule candidate counts reconcile with global `cand_tested`.

## Limits

This is one synthetic productive rule family with a supplied ledger and balanced mint/reweight paths. It tests the measured best order under actual effects; it does not establish a universal join-order heuristic, natural-task distribution, learning capability, or asymptotic complexity.
