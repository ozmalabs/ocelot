# RatioInduce direct-cost pilot preregistration — 2026-09-26

**Status:** Pilot, not confirmatory. No outcomes were inspected when this plan was written. This pilot estimates the direct native operator's cost envelope and validates its structural work counter; it does not test correctness of the inferred map (covered by the separate semantics probe), production closure, or natural-task tractability.

## Question

How does direct `RatioInduce` evaluation time and reported verification work scale with (a) population frame count, (b) relations per frame, and (c) number of coordinate dimensions, on exact common-ratio integer fixtures?

## Frozen design

- Entry point: Rust Term through `substrate_rs._native.Substrate.evaluate`.
- Codebook: one `ShapeSignature` with `dim_types` for each tested coordinate; no graph rule closure in timed region.
- Factors, varied one at a time:
  - frames `N ∈ {2, 8, 32, 128}`, holding 16 relations/frame and 2 coordinates;
  - relations/frame `P ∈ {4, 16, 64, 256}`, holding 16 frames and 2 coordinates;
  - coordinate dimensions `D ∈ {2, 3, 4}`, holding 16 frames and 16 relations/frame.
- Each population uses exact integer coordinate extents proportional across frames, yielding an explained result. All cases use the same family recipe; this is one positive synthetic family, not independent task diversity.
- One untimed warm-up per D, then seven timed repeats per cell. Fixed cell order as listed; pilot timing is descriptive and does not support inferential comparisons.
- Primary cost: per-call `perf_counter_ns`; secondary: per-call process CPU time; structural counter: `checked` from the output, expected `N × (D−1)`; correctness gate: `explained=true`, expected ratio triples, frame count, and checked count.
- Record raw per-call data, engine/native provenance and SHA-256 hashes of runner, protocol, native binary, Term/implementation source. Record process peak RSS once as a process-level high-water mark; do not attribute it to individual calls. Python allocation counts and native allocation counts are unavailable.
- No cases are excluded. A malformed output is retained and marked failure. No extrapolation beyond tested N/P/D.

## Analysis fixed in advance

For each factor level report median and p90 wall time, median CPU time, exact success count, `checked`, and ratio to the smallest level in its sweep. Report two-factor scaling separately from the one-factor sweeps; do not fit a universal polynomial from these points. Include payload relation count `N×P`, because population and per-frame sweeps both change total input size. The operator source loops over frame extents and dimensions, while tuple scanning occurs in coordinate extraction; the experiment can expose observed scaling but does not prove asymptotic complexity.

## Claim boundary

Even if times are smooth, this is a direct-call positive-fixture pilot on one CPU/runtime and an already materialized population. It excludes input extraction, feature generation, graph closure, population maintenance, rule scheduling, minting, redecode, reuse, high-boundary graph structure, false-positive rate, and natural workload prevalence. No commodity-hardware tractability or production economics claim follows.

## Run command

```sh
PYTHONPATH=.:runners/dsl/python python3 scripts/substrate_ratioinduce_cost_pilot_v1.py
```
