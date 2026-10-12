# Numeric opposition counterexample-guided synthesis v1 preregistration

Date: 2026-10-03

## Question

Can the substrate iteratively resynthesize a relation after each selected labeled counterexample, and does the resulting frozen hypothesis generalize beyond the query pool?

## Frozen protocol

Use the five training/query panels and source/build pins from the order-balanced numeric opposition active-query v1.1 lock. The learner starts with the four sparse labeled examples only. At each iteration it rebuilds a bounded version space from all labels acquired so far using `domains.generator.synthesize`, with `Neg`, `Eq`, `And`, no constants, maximum term size 9, a 12-second synthesis limit, 128 solutions, and the fixed 32-row unlabeled query pool as probes. The learner never receives the relation formula or holdout labels. If the candidate set is empty, halt as `no_fit`; if it is a singleton, halt as `singleton`; otherwise select a maximum-entropy query among unused pool rows, ask the local oracle for one label, append that counterexample, and resynthesize. Stop after six oracle calls or exhaustion of unused queries. Holdout scoring occurs only after the policy freezes its result.

Score the frozen candidate on the disjoint 1,296-case fractional grid from the upstream lock. Record every version-space candidate, query, oracle label, synthesis and selection time, halt reason, final candidate count, and holdout confusion counts. The target formula is available only to the outer oracle/scorer in the measurement harness. This is a source-locked harness separation, not a security boundary.

## Gates and limits

Require exact source/lock identity, unique query-pool membership, no query duplicated from initial training, oracle-label replay, per-round candidate fit to all revealed examples, stable source hashes, and independent final held-out rescoring. Report all five workers, including no-fit, timeout, ambiguity, and false-singleton outcomes. This measures iterative resynthesis for one authored relation and fixed grammar. It does not establish task invention, general model-adequacy detection, natural-task transfer, or autonomous self-improvement.
