# Thoughtexperiment FSDD matcher selection v1 — preregistration

## Question

Can graph-resident evidence selection choose among three substrate audio-matching Terms using held-out utterances from training speakers, then transfer the choice to disjoint speakers on real FSDD recordings? This tests a distinct modality and native matcher family after Omniglot visual matcher selection. The matchers and training labels remain harness supplied.

## Corpus and folds

Use the repository-local 3,000-WAV Free Spoken Digit Dataset release, with digits 0–9 and the six speakers parsed from filenames. Create three fixed folds by sorted speaker order: each worker holds out a disjoint pair and trains on the other four speakers. No speaker appears in both sides of a fold. For each training speaker and digit, use recording indices 0–4 as gallery templates and indices 5–9 as training queries. For each held-out speaker and digit, use indices 0–9 as evaluation queries. All queries are matched against the same 200-template gallery (20 templates per digit).

Compare three native graph Terms over the same 32×13 FSDD feature arrays: negative `DtwTo`, negative `PointSetDist`, and positive-similarity `XCorrPeak`. Use the repository’s frozen `fsdd_feat` and `load_wav` adapters. For each fold, score every training query with all three Terms, then submit prediction/truth evidence to `select_candidate_from_graph_evidence` inside a snapshot branch. Select the unique positive-evidence training maximum, return one compact ExperimentResidual, and verify candidate/evidence nodes do not leak into primary. Include tie and all-wrong abstention controls. Freeze orders and the selected Term before opening the held-out speaker clips for scoring.

## Measurements and gates

Report per-fold training and held-out accuracy by matcher, selected matcher, hindsight-best matcher, regret, per-speaker and per-digit counts, 10% chance, feature-preparation wall time, gallery build time, matcher time, query Term calls, exact query-by-gallery comparison count, snapshot/fork time, graph scoring time, residual-return time, and source/native/corpus hashes. Each fold has 200 training queries and 200 held-out queries; every query evaluates 200 gallery templates per matcher.

The 12-gate analysis requires: (1) all source/native/corpus hashes match; (2) all six speakers appear exactly once in a held-out pair across the three folds; (3) gallery, training-query, and held-out-query WAV identities are disjoint where required; (4) all three matchers score the identical query IDs and 200-template gallery; (5) feature matrices have the frozen 32×13 shape and every prediction belongs to 0–9; (6) training counts independently reproduce graph-Term evidence counts; (7) a unique training maximum is selected in every fold; (8) tie and all-wrong controls abstain; (9) held-out query identities/results do not appear in frozen orders; (10) selected matcher exceeds 10% chance in every fold; (11) selected matcher is within five percentage points of held-out hindsight best in every fold; and (12) branch isolation, compact residual return, and all cost fields pass integrity checks.

A passing result establishes a narrow speaker-transfer claim on six FSDD speakers and three fixed Terms. It does not establish population-level speech recognition, autonomous matcher invention, or general audio understanding. The corpus has only six speaker clusters; report fold and speaker-level outcomes rather than a nominal query-level confidence interval.

## Provenance and reproduction

Freeze this protocol, amendment history, runner, independent analyzer, FSDD feature adapter, matcher Terms, active Rust/Python sources, loaded native binary, and all 3,000 corpus file hashes before capture. Capture training orders first. Reconstruct held-out recording identities only in the later scoring stage. Preserve the raw per-query prediction matrix and do not overwrite earlier FSDD or grapheme-audio captures.
