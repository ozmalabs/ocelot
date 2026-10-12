# Omniglot substrate one-shot recognition current-source evaluation v1 (2026-09-29)

## Question

Can the current graph-Term recognizers identify held-out Omniglot character identities in a 20-way one-shot task, using an exemplar from one writer and queries from a different writer?

## Fixed protocol

- Use the local `strokes_evaluation` split only. Enumerate alphabets with at least 20 character classes; within each sampled alphabet, select 20 distinct character directories without replacement.
- Generate 100 episodes using NumPy `default_rng(7)`. In each episode, one writer supplies one exemplar for every selected class; a different writer supplies one query for each class. The writer pair and candidate classes are shared across all systems.
- Resample each trajectory to 64 points using `omniglot_world.trajectory(..., per_stroke=True)` and cache the same features for all systems.
- Score three existing substrate graph-Term systems: ordered DTW (`DtwTo`), point-set distance (`PointSetDist`), and deformable fit (`DeformDist`). For each episode and system, install one `Concept` exemplar per class in a fresh `Substrate`, then query every class with a `Mark`; predict the returned Concept name. No fitting, weight updates, test-time minting, threshold tuning, or post-hoc episode filtering is allowed.
- Add a deterministic uniform-random predictor as a task-level baseline. Its expected accuracy is 1/20=5%; report the realized accuracy on the same queries.

## Metrics and analysis

Report exact correct/total queries, episode accuracy, accuracy by alphabet, paired differences among systems, 95% percentile bootstrap intervals with alphabet as the resampling unit (10,000 deterministic bootstrap draws), random-baseline performance, and task/setup/evaluation wall and CPU time. Report process peak RSS and disclose that graph construction and Python dataset/trajectory loading are part of the measured cost. Do not treat queries within an episode or episodes from the same alphabet as independent replications.

## Integrity gates

Require the locked dataset manifest, current source/runtime hashes, stable pre/post inputs, exact 100-episode matrix, 20 unique classes per episode, distinct exemplar/query writers, 20 predictions per system/episode, valid candidate predictions, identical episode keys across methods, and independent score reconstruction from stored labels and predictions. Failed/refused predictions count as incorrect; no silent exclusions. The evaluator is the current graph-Term substrate route plus its host-side Omniglot adapter, not an end-to-end visual learner.

## Claim boundary

This measures selected training-free one-shot character recognition on one alphabet-balanced episodic protocol and one installed data split. It does not establish broad language competence, acquisition of new visual concepts, performance on scene images, or general learning capability. The episodes share the same alphabet inventory and must not be presented as 100 independent datasets.
