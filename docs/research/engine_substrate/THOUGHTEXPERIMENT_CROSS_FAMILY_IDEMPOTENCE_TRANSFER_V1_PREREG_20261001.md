# Thoughtexperiment cross-family idempotence transfer v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does a graph-authored candidate rank Program use an outcome from shape-axis deduplication to prioritize a structurally analogous recurrence-offer idempotence repair on a different target rule?

## Intervention

The shape-axis task trains the existing `dedup_identity_fix` outcome. A second task-specific candidate restores `Not Exists(candidate.has_mint_offer)` in a fault-injected `mrl_offer_due_once` rule. Both expose the shared candidate `outcome_class=idempotent_mint_guard`. `rank_candidates` aggregates class-level typed outcomes across target rules, while retaining target/label-specific history for candidates without a shared class. The authored score Program uses the existing prior-success/failure fields.

Each of three fresh workers runs one actual shape-axis correction training episode, then constructs two fresh recurrence-ledger task graphs: a cold graph with no `CorrectionOutcome` history and a transfer graph with typed records from the actually tried training candidates. Both graphs ground the graph-authored rank Program. Candidate ranking is followed by an independent task-specific branch oracle: try candidates in rank order on full-copy branches and accept the first branch that produces exactly one candidate-linked offer and reaches zero-progress native closure. Branch evaluation does not modify the primary.

## Gates

- Three fresh worker processes, with stable per-worker source/native fingerprints.
- Training episode adopts the shape-axis `dedup_identity_fix` and records its successful `idempotent_mint_guard` outcome.
- The recurrence candidate generator emits the distinct `mrl_offer_due_once` guard-restoration candidate with the shared outcome class.
- Cold graph has no outcome records; transfer graph has the training records.
- Transfer graph's candidate trace records cross-target prior success for the recurrence repair and ranks it before cold's first candidate.
- Both arms find a repair that passes the exactly-one-offer and fixed-point oracle.
- Primary rule/graph state remains unchanged through each branch evaluation.

## Interpretation limits

The two tasks share an explicitly authored `idempotent_mint_guard` class and known repairs. The experiment measures transfer of recorded utility through that representation, not discovery of the class, candidate, or utility label. It does not establish natural-task prevalence or autonomous experience transport. Candidate attempts and exact task utility are primary; timings are descriptive.
