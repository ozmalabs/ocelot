# Thoughtexperiment recurrence graph-selection v1.1 — preregistration

## Question

Does the graph-resident candidate-evidence scorer select a recurrence repair from the unchanged eight-candidate surface using correctly sampled training episodes, then generalize to disjoint held-out episodes?

## Sample unit and procedure

The sample unit is one fresh `MintingRecurrenceEpisode` containing two separately keyed due candidates. Run four source-locked workers. For every one of the eight unchanged `_default_candidates` variants, score four fresh training episodes per worker and four disjoint held-out episodes per worker (4 workers × 8 candidates × 4 episodes per split = 128 native candidate-episodes in each split). The independent episode oracle requires exactly one offer per due candidate and zero progress at fixed point. Training and held-out recurrence keys are disjoint by construction.

During `--orders`, run only training episodes. Convert each full-episode outcome to `correct` iff both offers equal one and final fixed-point progress is zero. Store the eight candidate descriptors and their four training labels in CandidateProposal/CandidateEvidence nodes on an isolated snapshot branch. The native Term must select a unique positive-evidence maximum. Return only its digest and training-match count to primary. Freeze all descriptors, training outcomes, graph decision, and source hashes. The orders artifact must contain no held-out output or held-out recurrence key.

Only after orders are written, `--score` runs the held-out episodes for every candidate in fresh substrate instances. It compares the previously selected digest against held-out outcomes; it does not rerank candidates.

## Pass conditions and limits

Pass requires identical eight-candidate descriptors across workers; the same unique `dedup_identity_fix` winner with 4/4 correct train episodes in every worker; each alternative below four; 4/4 held-out success for each selected winner; each alternative failing at least one held-out episode; strict train/held-out key separation; valid fixed points; unchanged primary rules; one compact residual per worker; and no candidate/evidence leakage. Report candidate generation, episode execution, graph-Term scoring, and held-out costs separately.

This is one recurrence family with an authored fault, generic host-side candidate generator, and known task oracle. It measures selection and reuse within that family, not open-ended candidate invention, cross-family learning, or oracle trust.

## Reproduction

Run the source-locked runner with `--lock`, `--orders`, and `--score`, in order, then run the independent analyzer. Held-out execution must not begin until the frozen orders artifact exists.
