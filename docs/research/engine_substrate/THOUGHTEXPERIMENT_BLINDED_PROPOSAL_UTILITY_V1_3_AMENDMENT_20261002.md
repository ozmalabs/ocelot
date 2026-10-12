# Thoughtexperiment blinded proposal utility v1.3 — exhaustive held-out scoring amendment

**Date:** 2026-10-02  
**Reason:** The completed v1 descriptive panel failed the preregistered exhaustive held-out-scoring gate: policy scoring stopped after its first passing candidate and covered 70/104 held-out candidate instances. This amendment specifies a new source-locked v1.1 capture. It does not alter, repair, or upgrade the v1 result.

## Confirmatory rerun

Retain the four admitted families, four fresh workers per family, unchanged candidate generation, five policies, randomization seeds, training data construction, candidate descriptors, oracles, and primary-state/receipt checks from v1. The v1.1 runner, adapter, rank-policy implementation, this amendment, original protocol, randomization/cost amendment, task files, engine sources, native binary, and seed inputs must be captured in a new immutable lock before any order or score capture.

As in v1, the order workers see training outcomes only and write every complete policy order before held-out scoring starts. The order capture must be inspected for worker/family completeness, valid permutations, seed schedule, stable source hashes, and absence of held-out outcome fields before the scoring command is run.

For each held-out worker/family context, the independent scorer evaluates every frozen candidate exactly once on an isolated branch from the same unchanged primary and the same held-out cases. It stores a complete candidate-to-outcome matrix, including task cases, utility, applied-rule receipt, primary preservation, and branch/patch/scoring/verification timings. The scorer then derives each policy's first-success prefix by looking up the matrix in the already frozen order; it must not expose any outcomes to the order worker or change the recorded order.

Report two distinct costs:

1. **Policy selection cost:** context/enumeration, policy-order construction, required training acquisition, and only the candidate-trial prefix through the first passing candidate, reconstructed from per-candidate timings.
2. **Exhaustive audit cost:** the additional held-out branches needed to score candidates that a policy would not try after its first success. This cost validates the complete outcome matrix and is not a free operational capability or a production saving.

The primary analysis remains paired first-candidate utility and candidate trials by worker/family, with each family shown separately. Report cost comparisons only with both policy-selection and exhaustive audit costs explicit. Any incomplete candidate matrix, source drift, invalid receipt, primary mutation, or order/score mismatch fails the confirmatory gate; preserve the capture and report the failure.

## Interpretation boundary

Passing this gate can establish the measured value of graph-resident experience-conditioned ordering over the authored candidate set and task families. It cannot establish autonomous candidate generation, oracle discovery, open-ended self-improvement, natural-task prevalence, or broad general capability. Candidate-space expansion remains a separate next delegation gate.
