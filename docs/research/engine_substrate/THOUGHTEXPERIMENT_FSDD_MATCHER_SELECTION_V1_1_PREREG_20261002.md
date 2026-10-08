# Thoughtexperiment FSDD matcher selection v1.1 — preregistration

## Amendment and validity boundary

The v1 training capture established its training decisions, including an exact ordered-DTW/PointSetDist tie in fold 0. Its held-out scoring capture is invalid: the runner built an empty candidate gallery in the scoring phase, producing `None` predictions for all 600 queries. The v1 orders and failed score capture are retained unchanged as a pilot and are not evidence about held-out recognition. This repaired run keeps the same six-speaker folds, training templates (indices 0–4), and training queries (indices 5–9). To avoid reusing any held-out recording already loaded by the failed pilot, evaluation uses only held-out-speaker indices 10–19. The scoring phase explicitly loads the frozen 200-template training gallery before evaluating held-out queries. This correction and the changed query indices were fixed before repaired held-out scoring.

## Question

Can graph-resident evidence selection choose among three substrate audio-matching Terms using held-out utterances from training speakers, then transfer the choice to disjoint speakers on real FSDD recordings? This tests a distinct modality and native matcher family after Omniglot visual matcher selection. The matchers and training labels remain harness supplied.

## Corpus and folds

Use the repository-local 3,000-WAV Free Spoken Digit Dataset release, with digits 0–9 and six speakers parsed from filenames. Create three fixed folds by sorted speaker order: each fold holds out a disjoint pair and trains on the other four speakers. For each training speaker and digit, use indices 0–4 as gallery templates and 5–9 as training queries. For each held-out speaker and digit, use indices 10–19 as evaluation queries. The 200 training gallery templates (20 per digit) are reused unchanged for held-out scoring. No query recording is a gallery template.

Compare three native graph Terms over identical 32×13 FSDD feature arrays: negative `DtwTo`, negative `PointSetDist`, and positive-similarity `XCorrPeak`. Use the repository's frozen `fsdd_feat` and `load_wav` adapters. For each fold, score every training query with all three Terms, then submit prediction/truth evidence to `select_candidate_from_graph_evidence` inside a snapshot branch. Select the unique positive-evidence training maximum, return one compact `ExperimentResidual`, and verify candidate/evidence nodes do not leak into primary. Include tie and all-wrong abstention controls. Freeze orders and the selected Term before loading the new held-out query indices.

## Measurements and gates

Report per-fold training and held-out accuracy by matcher, selected matcher, hindsight-best matcher, regret, per-speaker and per-digit counts, 10% chance, feature-preparation wall time, gallery build time, matcher time, query Term calls, exact query-by-gallery comparison count, snapshot/fork time, graph scoring time, residual-return time, and source/native/corpus hashes. Each fold has 200 training queries and 200 held-out queries; each query is compared against 200 gallery templates per matcher.

The 12 gates require: (1) all source/native/corpus hashes match; (2) all six speakers appear exactly once among the held-out pairs; (3) gallery, training-query, and held-out-query WAV identities are disjoint; (4) all matchers score identical query IDs against the same gallery; (5) all predictions are valid digits and the feature adapter enforces 32×13 arrays; (6) training accuracy recomputes the graph evidence counts and decisions; (7) a unique training maximum is selected in every fold; (8) tie and all-wrong controls abstain; (9) held-out identities and results are absent from frozen orders; (10) selected matcher exceeds 10% chance in every fold; (11) selected matcher is within five points of held-out hindsight best in every fold; and (12) branch isolation, compact residual return, and all cost fields pass integrity checks.

The v1 training capture already showed that fold 0 has no unique winner. This is retained as an expected empirical gate failure; no tie-breaker is introduced. The repaired scoring still measures the three supplied matchers on the fresh held-out recording indices, while the report distinguishes matcher performance from the failed per-fold selection gate. A passing result would establish only a narrow speaker-transfer claim on six speakers and three fixed Terms, not autonomous matcher invention, population-level recognition, or general audio understanding. With six speaker clusters, report fold and speaker outcomes, not query-level confidence intervals.

## Provenance and reproduction

Freeze this amendment, runner, independent analyzer, source adapter, matcher Terms, active Rust/Python sources, loaded native binary, and all 3,000 corpus file hashes before repaired capture. Capture training orders first. The frozen orders contain no held-out query identities. The score phase loads only the existing training gallery and the new held-out query indices 10–19, then retains the full per-query prediction matrix. Preserve the invalid v1 pilot unchanged.
