# Thoughtexperiment FSDD matcher selection v1.2 — preregistration

## Amendment and validity boundary

The v1 orders are retained as a valid training-only pilot. Its score capture is invalid because the held-out scoring runner supplied no gallery; all predictions were `None`. The v1.1 attempt corrected the gallery logic and produced a fresh training-order capture, but failed before loading any held-out audio: it attempted to index a `Path` as a mapping while assembling feature paths. Its lock/orders are preserved and excluded from result claims. This v1.2 capture fixes that path expression. It uses the original frozen training/evaluation assignment from v1.1: training gallery indices 0–4, training queries 5–9, and held-out queries 10–19 on two disjoint speakers per fold. The failed v1.1 scoring process did not read or transform held-out recordings. No held-out query features or predictions have been observed for indices 10–19 before this preregistration.

## Question and method

Can graph-resident evidence selection choose among three substrate audio-matching Terms using held-out utterances from training speakers, then transfer the choice to disjoint speakers on real FSDD recordings? This tests a distinct modality and native matcher family after Omniglot visual matcher selection. The matchers and training labels remain harness supplied.

Use the repository-local 3,000-WAV Free Spoken Digit Dataset release, digits 0–9, six speakers, and three fixed folds from sorted speaker order. Each fold holds out two speakers and trains on four. Each fold has 200 training gallery templates, 200 training queries, and 200 held-out queries. Every query is scored against the same gallery of 20 templates per digit. Compare native graph Terms for negative `DtwTo`, negative `PointSetDist`, and positive-similarity `XCorrPeak`, over the frozen 32×13 `fsdd_feat` arrays.

For every training query, score all three Terms and submit prediction/truth evidence to `select_candidate_from_graph_evidence` inside a snapshot branch. Select the unique positive-evidence training maximum, return one compact `ExperimentResidual`, and verify candidate/evidence nodes do not leak into primary. Include tie and all-wrong abstention controls. Freeze orders and decisions before loading the new held-out query recordings. In held-out scoring, load exactly the frozen training gallery templates and held-out query recordings; no held-out data contributes to gallery contents or selection.

## Measurements and gates

Report per-fold training and held-out accuracy by matcher, selected matcher, hindsight-best matcher, regret, per-speaker and per-digit counts, 10% chance, feature-preparation wall time, gallery build time, matcher time, query Term calls, exact query-by-gallery comparison count, snapshot/fork time, graph scoring time, residual-return time, and source/native/corpus hashes. Each fold has 200 training and 200 held-out queries; every query evaluates 200 gallery templates per matcher.

The 12 gates are: (1) source/native/corpus hashes match; (2) all six speakers appear exactly once among held-out pairs; (3) gallery, training-query, and held-out-query WAV identities are disjoint; (4) all matchers score identical queries against identical galleries; (5) predictions are valid digits and the frozen feature adapter enforces 32×13 arrays; (6) training accuracy recomputes graph evidence counts and decisions; (7) a unique training maximum is selected in every fold; (8) tie and all-wrong controls abstain; (9) held-out identities/results are absent from orders; (10) selected matcher exceeds 10% chance in every fold; (11) selected matcher is within five points of held-out hindsight best in every fold; (12) branch isolation, compact residual return, and cost fields pass integrity checks.

The v1 training capture already showed an exact tie in fold 0. That gate remains an expected empirical failure; no tie-breaker is introduced. Report matcher outcomes even if selection abstains, and distinguish those outcomes from successful end-to-end selection. A passing result supports only a narrow speaker-transfer claim across six speakers and three fixed Terms. Do not report query-level confidence intervals with six speaker clusters.

## Provenance and reproduction

Freeze this preregistration, runner, independent analyzer, source adapter, matcher Terms, active Rust/Python sources, loaded native binary, and all 3,000 corpus file hashes before capture. Capture training orders first; verify they contain no held-out query identities. Then run the score phase, which loads the frozen gallery and only the new held-out recordings (indices 10–19). Preserve all v1 and v1.1 pilot artifacts unchanged.
