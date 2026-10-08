# Omniglot disjoint-background one-shot transfer v1 preregistration (2026-09-29)

## Question

Do the three frozen graph-Term recognizers retain their one-shot character recognition behavior on Omniglot's background alphabet split, which is disjoint from the evaluation alphabets in the prior locked panel?

## Fixed protocol

- Use all background alphabets containing at least 20 character classes. Confirm alphabet names are disjoint from all evaluation-split alphabets before capture.
- Generate 100 20-way episodes using the same episode-generation protocol and NumPy `default_rng(7)`: choose an eligible alphabet uniformly, choose 20 character identities without replacement, draw one exemplar writer and a distinct query writer, and query each of the 20 classes.
- Use the same 64-point, per-stroke trajectory adapter and the same ordered DTW, point-set, and deformable graph Terms from the prior evaluation-split panel. Terms are frozen; no fitting, updates, threshold tuning, or minting.
- Share episode keys and candidate/query data across all three recognizers. Compare to a deterministic uniform-random predictor (5% chance).

## Metrics

Report exact correct/total, alphabet-cluster bootstrap 95% intervals with 10,000 draws, paired method differences, performance by alphabet, random control, median episode wall/CPU time, shared feature preparation, total run cost, and peak RSS. Bootstrap over alphabets, not individual queries or episodes.

## Integrity gates

Require exact background dataset manifest, source/runtime hashes, frozen evaluation-panel lock/results hashes, disjoint alphabet sets, exactly 100 episodes and 300 system/episode rows, 20 distinct candidates per task, distinct writer IDs, shared episode keys, valid candidate predictions, independent score reconstruction, and pre/post input stability. Refusals count as errors; malformed outputs fail the integrity gate.

## Claim boundary

This is a transfer evaluation of existing one-shot application behavior across disjoint alphabet populations with no model training. It does not test learning across alphabets, concept acquisition, different modalities, or general capability. Background/evaluation distinction is treated as a dataset split, not as a random sample of all writing systems.
