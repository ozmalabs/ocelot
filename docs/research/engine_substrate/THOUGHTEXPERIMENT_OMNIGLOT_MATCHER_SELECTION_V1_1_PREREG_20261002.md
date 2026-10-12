# Thoughtexperiment Omniglot matcher selection v1.1 — preregistration

## Question

Can graph-resident evidence selection choose among existing substrate Term matchers from real Omniglot background-alphabet episodes, then transfer that choice to disjoint evaluation alphabets? This measures application of held matcher structure and isolated experiment reporting; candidate matchers and training labels remain supplied by the harness.

## Task and paired design

Compare `ordered_dtw`, `pointset`, and `deformable` from `domains/recognition_graph.py`. Generate 40 one-shot, 20-way episodes per worker for the official Omniglot `background` split, using three workers with fixed, distinct seeds. Each episode chooses one alphabet, twenty character classes, one exemplar drawing per class, and query drawings from a different writer. All matchers use identical training episodes. The two official split alphabets must be disjoint; hash every source and dataset byte before capture.

Score all three matchers on all background training queries. Build CandidateProposal and CandidateEvidence nodes in a snapshot fork; pass only background prediction/truth pairs as evidence to the graph Term. Select the unique positive-evidence maximum. Return one compact ExperimentResidual with the selected matcher ID and training input digest to primary. Candidate/evidence nodes must remain branch-local. Tie and all-wrong controls must abstain. The order artifact contains training specs/outcomes and the selected matcher only; it contains no evaluation specs, labels, or predictions.

Only after freezing training orders, deterministically generate 40 evaluation-split episodes per worker from a separate fixed seed. Evaluate all three matchers on the same support/query drawings. Report per-worker training and held-out accuracy by matcher, selected-matcher accuracy, hindsight-best matcher and regret, accuracy relative to 5% chance, exact Term-call counts, train/evaluation feature-preparation time, matcher evaluation time, snapshot/fork time, graph-Term scoring time, and residual-return time. Keep alphabet-level outcomes so uncertainty can be clustered by alphabet. Three worker seeds are repetitions, not independent datasets.

## Gates

The 12-gate analysis requires: (1) source, native, protocol, and full local dataset hashes match the lock; (2) background/evaluation alphabets are disjoint; (3) three fresh workers and distinct episode seeds are present; (4) exact episode/support/query identity is shared across matcher candidates; (5) training evidence is complete and selector count equals independently recomputed accuracy; (6) the graph Term chooses the unique training maximum in every worker; (7) tie and all-wrong controls abstain; (8) orders contain no evaluation specs, labels, or outcomes, and evaluation scoring begins only after orders freeze; (9) selected matcher accuracy exceeds 5% chance in each worker; (10) selected-matcher regret is at most five percentage points versus the held-out hindsight best in each worker; (11) no CandidateProposal/CandidateEvidence nodes leak to primary and exactly one compact residual returns; and (12) all preregistered cost measures are present, finite, and recomputable from raw rows.

The candidate matchers are supplied; labels and episode construction are harness-defined. Even a passing transfer result is not autonomous visual concept or matcher invention.

## Provenance and reproduction

Freeze protocol, amendment, runner, independent analyzer, active Python/Rust sources, loaded native binary, and all files in both Omniglot splits. Capture training orders first; held-out specs and outcomes are produced only by the later scoring stage. The analyzer consumes the lock, orders, and scores independently of the runner. Preserve per-query predictions, episode digests, and phase-specific timing. Never overwrite the v1 pilot or any existing capture.
