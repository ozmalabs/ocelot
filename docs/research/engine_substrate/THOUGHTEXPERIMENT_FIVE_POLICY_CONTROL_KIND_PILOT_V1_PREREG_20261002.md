# Thoughtexperiment five-policy control-kind pilot v1 — preregistration

**Date:** 2026-10-02  
**Question:** On the held-out control-kind classification task, how do the production graph ranker's cross-family experience order and four baselines compare when candidate orders are frozen before the held-out oracle runs?

## Scope

This is a four-worker, one-family integration pilot for the five-policy order core. It is not the confirmatory four-family panel and cannot establish general transfer. For each worker, candidate generation and training utility use the unchanged _default_candidates path and the fixed control-kind train names. The existing three-family training records for recurrence, navigation, and shape-axis are consumed only as training evidence by the experience arm. Control-kind training records are reserved for the target-memoization arm.

## Policies and information boundaries

1. Experience rank: production graph rank Program receives the three other families' train-only outcomes.
2. Frozen rank: same graph Program and target candidate set with zero outcome history.
3. Default: unchanged generator order.
4. Random: deterministic shuffle using preregistered worker seeds 420001–420004.
5. Target memoization: best successful training candidate for exact target identity; ties follow default order.

The order artifact contains descriptors, candidate bundles, training-record source names, traces, and orders. It must contain no held-out outputs, utility, or scorer results. A separate score stage reads the frozen orders and scores candidates sequentially on the two fixed held-out control names, stopping after the first successful candidate in each arm.

## Measures and limits

Record first-candidate utility, candidate attempts to first held-out success, rank time, and per-trial elapsed time. Per-trial time includes fresh task setup and the direct control-name oracle; it does not isolate branch construction, adoption, or verification costs. Therefore this pilot makes no economic advantage claim. Report every worker and arm, including unresolved or unsuccessful search.

## Integrity gates

- Source-lock this protocol, runner, order-policy core, control task source/seed, four-family training source captures, ranker/native source and binary.
- Four fresh rank-order worker processes and four separate score worker processes.
- Candidate descriptors match across workers; all arms use the same candidates.
- Experience records contain only the three other families; target memo records contain only control-kind training outcomes.
- Orders are persisted before any held-out scoring; score capture binds to the exact order-file hash.
- Primary ranker order capture stores no held-out utility fields.

Passing validates one-family integration only. Full panel capture remains gated on all four families, four workers each, and the preregistered complete cost ledger.
