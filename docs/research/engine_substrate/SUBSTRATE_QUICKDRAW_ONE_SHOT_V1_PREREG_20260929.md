# QuickDraw one-shot shape recognition v1 preregistration

**Lock date:** 2026-09-29, before the confirmatory run. **Question:** can the three frozen graph-Term recognizers distinguish new single-stroke QuickDraw shape drawings from one exemplar per class, using the current native graph-Term route?

## Data and task

Use the locally retained QuickDraw NDJSON files in `data/pendata` for the eight fixed classes `circle`, `square`, `triangle`, `line`, `zigzag`, `star`, `hexagon`, and `octagon`. These classes were selected because each has a large one-stroke subset and together include curved, polygonal, and linear shapes. Parse valid drawings with `domains.pen_world.load_quickdraw_drawings`; exclude drawings with other than one stroke. Convert the stroke to 64 points with `domains.glyph_motor_world.to_trajectory`, which arc-length resamples, centers, and unit-scales it. Record all valid, malformed, and excluded counts.

Generate 100 episodes with NumPy `default_rng(20260929)`. Every episode uses all eight classes, one support drawing per class, and five query drawings per class, sampled without replacement within each class. The eight supports and 40 queries are shared by all three systems. Each episode therefore has 8-way choice and 40 labeled queries. Drawing IDs may recur across separate episodes; they never overlap between support and query within an episode. A deterministic uniform-random predictor is the chance baseline (12.5%).

## Systems and capture

Evaluate the existing ordered DTW (`DtwTo`), point-set (`PointSetDist`), and deformable (`DeformDist`) graph Terms without fitting, updating, minting, threshold tuning, or post-hoc exclusions. Use a fresh native `Substrate` per system/episode, with one `Concept` candidate per class and five `Mark` queries per class. Capture every support/query key, prediction, random prediction, accuracy, candidate/query counts, wall/CPU time, peak RSS, feature-preparation cost, runtime/source/data hashes, and pre/post source stability. Append JSONL records; do not rewrite earlier records.

## Analysis and integrity gates

An independent analyzer must verify the locked current source/native/data inputs, source stability, exactly 100 episodes and 300 system/episode workers, shared episode designs across systems, eight distinct candidate classes, 40 queries per worker, within-episode support/query disjointness, prediction membership and accuracy reconstruction, and complete random controls. Report query accuracy and per-class accuracy, paired system differences, class-cluster bootstrap 95% intervals (10,000 draws; seed 20260930), random accuracy, median worker wall/CPU time, peak process RSS, feature-preparation time, and total capture cost. Classes, rather than individual drawings or repeated episodes, are the uncertainty clusters.

The retained NDJSON files are bounded samples, and some end with one malformed truncated record; the loader's skip count must be disclosed. The files expose drawing IDs but no contributor/writer identifiers. This test therefore measures recognition of new drawings from the fixed classes, not writer-disjoint transfer, novel-class learning, or population-level QuickDraw accuracy. It measures the native graph-Term scorer plus host-side data loading/trajectory preparation, not an end-to-end visual learner.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_quickdraw_one_shot_v1.py --lock
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_quickdraw_one_shot_v1.py
python3 scripts/analyze_substrate_quickdraw_one_shot_v1.py
```
