# Numeric opposition relation learning v1.1 — coverage-directed preregistration

Date: 2026-10-03

## Question

Does explicit training coverage of both coordinate dimensions improve the
substrate synthesizer's held-out generalization, relative to the previous
random balanced panel (1/5 exact on the same held-out grid)?

## Frozen design

Run five fresh workers through the same `domains.generator.synthesize` path,
fixed grammar (`Neg`, `Eq`, `And`), no constants, maximum size 9, and 12-second
budget. Each training set has 16 labeled examples: eight positives and eight
negatives. Every set includes positive x-axis, y-axis, and two-dimensional
vectors; its negative controls include an x-only match and a y-only match,
plus six non-opposition pairs. Remaining positive values and negative controls
vary deterministically by worker seed. The learner receives only training
examples and never receives the target formula or held-out grid.

After synthesis is complete, evaluate the frozen term on the same 1,296
fractional vector pairs as v1. Compare exact-generalization rate, false
positive/negative counts, explored terms, term size, and CPU/wall time with the
captured random-panel v1 cohort. This is a design comparison rather than a
paired per-worker causal estimate; the training distributions differ by
construction.

## Validity and interpretation

All workers must preserve their frozen training panels and source/build
identity. Score every returned term, including underfit hypotheses. No
held-out resynthesis or worker exclusion. A higher exact rate would support
the value of axis-separating examples for this one fixed relation and grammar;
it would not establish an active counterexample policy, broad sample
efficiency, or general learning capability.
