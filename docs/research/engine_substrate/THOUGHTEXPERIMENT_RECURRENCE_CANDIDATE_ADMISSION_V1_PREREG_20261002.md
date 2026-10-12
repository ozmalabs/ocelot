# Recurrence candidate-admission audit v1 — preregistration

**Date:** 2026-10-02  
**Question:** Does the unchanged correction generator provide a sufficiently diverse and behaviorally measured candidate set for the recurrence-offer idempotence task to qualify as a family in the blinded ranker panel?

## Scope and fixtures

This is a fixture-admission audit, not a ranker comparison. Three fresh workers independently construct the same recurrence rule fault: remove the candidate-scoped `Not` guard from `mrl_offer_due_once`. The unchanged `_default_candidates` function enumerates the applicable edits. Each generated candidate is applied in fresh substrate instances and scored on both a training episode and a disjoint held-out episode. Each episode presents two separately keyed due candidates; the independent oracle requires exactly one mint offer for each and zero rule work at fixed point. Candidate outcome labels are not supplied to a ranking Program.

The worker and split identifiers are fixed before capture. Candidate descriptors are canonicalized by removing generated variant rule names and hashing the remaining rule bundles; all workers must produce the same ordered descriptor set. The audit records every candidate's train and held-out outcome, not only candidates tried before the first repair succeeds.

## Admission gates

- Three fresh workers and exact source/native fingerprint parity with the pre-capture lock.
- At least three unique applicable candidate bundles from the unchanged generator, with candidate descriptors identical across workers.
- Every candidate receives a complete training and held-out task-oracle score.
- At least one candidate passes both held-out cases and at least one fails.
- Train and held-out recurrence keys are disjoint, and both task episodes begin from fresh substrate instances.
- The oracle is recomputed from per-candidate offer counts and native fixed-point progress.

Passing these gates admits recurrence as a candidate-utility fixture for a later blinded panel. It does not establish ranker quality, economic benefit, cross-family transfer, or autonomous task/candidate discovery. Full cost accounting remains a separate requirement of the confirmatory panel.
