# Omniglot graph-Term candidate/trajectory scaling v1 preregistration (2026-09-29)

## Question

How do held-structure recognition accuracy and per-episode cost change as the same Omniglot task varies candidate-set size and trajectory resolution?

## Frozen input panel

Reuse all 100 episode definitions from the locked Omniglot current-source v1.2 capture: the same 20 alphabets, selected character identities, exemplar/query writer pairs, and episode ordering. Candidate sets are nested prefixes of each episode's preselected 20 classes at k={5,10,20}; query labels are the same prefix, so each k-way task has k queries. Chance is 1/k. Resample the same underlying trajectories to L={16,32,64} points with the current per-stroke trajectory adapter. No model is fit and no thresholds or Terms are changed.

Cross candidate size k={5,10,20}, trajectory length L={16,32,64}, and the three frozen graph-Term recognizers (`DtwTo`, `PointSetDist`, `DeformDist`). Each system/episode/condition uses a fresh Substrate with k exemplars and queries every one of the k selected classes. A deterministic uniform-random prediction sequence is shared across the three recognizers within each matched episode/condition.

## Metrics

Report accuracy and alphabet-clustered percentile bootstrap 95% intervals (10,000 deterministic draws) for every system/way/length cell, matched accuracy differences, random-control accuracy, median/p95 worker wall and CPU time, peak RSS, shared feature-preparation cost, and total capture cost. Each query compares against k candidate exemplars; the `Argmax` Terms imply k² distance-operator evaluations per episode. Report this as a source-derived count, separate from measured native operation counters, which are not exposed in this harness.

The initial v1 capture completed all 2,700 worker rows with stable sources, but its offline analyzer stopped before analysis because the runner source-validation helper was not bound in the analyzer scope. The raw capture is preserved as exploratory. V1.1 binds the correct runner/analyzer pair, regenerates the source lock, and repeats the same frozen matrix.

## Integrity gates

Require exact v1.2 episode-panel reuse, current source/runtime/dataset and previous-panel lock hashes, stable pre/post inputs, complete 2,700-cell matrix, 100 episodes per condition, nested class identities, writer separation, shared random controls, valid prediction reconstruction, and exact independent accuracy/count reconstruction. Refusals and wrong outputs count as errors; incomplete or malformed rows fail the integrity gate. The output remains a benchmark of the selected Term/adapter route, not a general substrate asymptotic theorem.
