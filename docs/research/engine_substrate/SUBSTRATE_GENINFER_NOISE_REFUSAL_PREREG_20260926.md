# GenInfer positive recovery and null-refusal preregistration (2026-09-26)

## Question

Across the four tested invertible 2-D maps, does GenInfer recover the exact generator on positive observations and refuse four fixed non-linear/noise/coverage violations rather than returning a spurious generator?

## Factorial conditions

Cross each locked transform from [`SUBSTRATE_GENINFER_TRANSFORM_FAMILY_PREREG_20260926.md`](SUBSTRATE_GENINFER_TRANSFORM_FAMILY_PREREG_20260926.md) with five observation conditions: `positive`; `origin_corrupt` changes only predicate p0's target coordinate from `(0,0)` to `(1,0)` (no linear map sends the origin there); `predicate_corrupt` changes target p3's predicate to `corrupt_p3`; `missing_origin` removes target p0; `extra_origin` adds an unmatched `extra:(0,0)` relation. All use the same four unique-predicate source relations, and each target retains data-derived B=4. Missing/extra cases intentionally have 3/5 observed relations against four held relations.

Run four families × five conditions, one fresh native substrate per source family, five timed direct calls per cell, with a fixed-seed shuffled schedule per repetition. Time `GenInfer(field=explained)`; read `matrix` and `checked` outside the timed interval. One untimed positive warm-up precedes measurements. Every cell must check 6,560 candidates.

## Gates and analysis

Independent analysis verifies all 20 cells, five repetitions, exact generated signatures/targets, relation counts, B=4 and the 6,560 candidate count, exact matrix recovery for positive cases, `explained=false` and empty matrix on all four null classes, finite timings, deterministic balanced schedule, and current source/native hashes. Report latency by condition/family. No timing threshold is set.

## Claim boundary

This is positive and selected-null behavior for four small 2-D integer-linear transforms with unique predicates. It does not sample realistic observation noise, missingness distributions, nonlinear families, higher dimensions, full graph-authored minting/closure, or natural tasks. One corrupted-origin control tests a hard linear invariant, not calibrated false-positive probability.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_noise_refusal_probe_v1.py
python3 scripts/analyze_substrate_geninfer_noise_refusal_probe_v1.py
```

## Amendment after diagnostic capture (2026-09-26)

The first capture revealed that `origin_corrupt` is not a valid null for this operator: GenInfer origin-normalizes coordinate axes, so a translated copy remains admissible. The v1 capture is retained as a failed gate and is evidence of translation invariance. The confirmatory v2 control replaces it with `point_corrupt_p1`, which increments the first target coordinate for p1 only. This violates the linear relation among the observed points without relying on an absolute origin. Other conditions and the schedule design remain fixed. V2 files carry distinct `v2` run IDs and outputs; they do not overwrite the v1 diagnostic.
