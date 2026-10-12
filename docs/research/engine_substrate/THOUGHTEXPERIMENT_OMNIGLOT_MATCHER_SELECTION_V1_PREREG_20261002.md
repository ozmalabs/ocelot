# Thoughtexperiment Omniglot matcher selection v1 — preregistration

## Question

Can graph-resident evidence selection choose among existing substrate Term matchers from real Omniglot background-alphabet episodes, then transfer that choice to disjoint evaluation alphabets? This measures application of held matcher structure and isolated experiment reporting; the candidate matchers and labels remain supplied by the harness.

## Task and paired design

Compare the existing `ordered_dtw`, `pointset`, and `deformable` matchers from `domains/recognition_graph.py`. Generate 40 one-shot, 20-way episodes per worker for both the official `background` and `evaluation` Omniglot splits. Use three workers with fixed, distinct episode seeds. Each episode chooses one alphabet, twenty character classes, one exemplar drawing per class, and query drawings from a different writer. All matcher predictions on an episode use the identical support/query drawings. The two split alphabets must be disjoint, and all source and dataset bytes are hashed before capture.

Score each matcher on all background training queries. Build one CandidateProposal per matcher and CandidateEvidence per query in a snapshot fork; pass only predictions and background truth labels as training evidence. The native graph Term selects a unique positive-evidence maximum. Return a compact ExperimentResidual with the selected matcher ID and training input digest to the primary graph. Candidate/evidence nodes must remain branch-local. Run tie and all-wrong controls to verify abstention. Freeze the orders and selected matcher before running any evaluation-split matcher outcomes.

After orders freeze, evaluate all three matchers on every sealed evaluation episode. Report per-worker training and held-out accuracy by matcher, selected-matcher accuracy, hindsight-best matcher and regret, accuracy relative to 5% chance, total Term calls, graph scoring time, branch-fork time, residual-return time, feature-preparation time, and end-to-end matcher evaluation time. Keep alphabet-level outcomes so uncertainty can be clustered by alphabet; three worker seeds are repetitions, not independent datasets.

## Gates

The 12-gate analysis requires: (1) source, native, protocol, and full local dataset hashes match the lock; (2) background/evaluation alphabets are disjoint; (3) three fresh workers and distinct episode seeds are present; (4) exact episode/support/query identity is shared across matcher candidates; (5) training evidence is complete and selector count equals independently recomputed training accuracy; (6) the graph Term chooses the unique training maximum in each worker, or records a gate failure; (7) tie and all-wrong controls abstain; (8) held-out results are absent from orders and were evaluated only after orders freeze; (9) selected matcher accuracy exceeds 5% chance in each worker; (10) report selected-matcher regret to the held-out hindsight best without treating the latter as an available choice; (11) no CandidateProposal/CandidateEvidence nodes leak into primary and exactly one compact residual returns; and (12) all cost measures are finite and recomputable from raw rows.

The cross-split transfer outcome is empirical: require no more than five percentage points of held-out accuracy regret versus the hindsight-best matcher in each worker for a transfer pass. Failure leaves the source-backed selection mechanism measured but rejects this transfer gate. The dataset contains handwritten character images, but the episode sampler and matcher vocabulary are fixed; this is not autonomous visual concept discovery or broad vision capability.

## Provenance and reproduction

Freeze protocol, runner, independent analyzer, active Python/Rust sources, loaded native binary, and every file in both Omniglot splits. Capture training orders and branch receipts first; score held-out only after the order file is immutable. The analyzer consumes the frozen lock, orders, and scores, and does not call the runner. Preserve full per-query predictions and hashes. Do not overwrite any existing capture.

