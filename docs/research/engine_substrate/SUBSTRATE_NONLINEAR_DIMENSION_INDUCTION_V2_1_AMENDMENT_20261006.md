# Bounded quadratic GenInfer v2.1 amendment

This amendment is frozen before the v2.1 runner, analyzer, source lock, or
confirmatory captures. It corrects one fixture overlap discovered while
constructing the harness; the engine hypothesis class and learner are
unchanged.

## Transfer-point correction

The original preflight transfer set included `(4,1)`, which is also one of the
two overdetermining training-validation points. Replace it with `(5,1)`. The
v2.1 transfer set is therefore `(2,1),(1,3),(3,2),(2,3),(5,1),(3,3)`. Every
transfer coordinate is now disjoint from the seven training coordinates.

The operator is defined on frame-local coordinates: each axis is normalized
by that frame's minimum before applying the polynomial. The held-out oracle
must therefore evaluate the same polynomial at `(x-min_x,y-min_y)` for the
held-out frame. This is required for nonlinear maps because shifting the input
origin changes non-constant polynomial terms; the linear positive control's
shift is represented by the existing translation residual. The preregistered
runner had initially compared against global-coordinate quadratic outputs and
correctly failed after reload. That smoke failure is preserved as fixture
diagnosis, not confirmatory evidence. The preflight now records the held-out
frame origin and normalized oracle outputs.

## Audit parity workers

Retain the original 160 clean semantic workers: eight registered conditions,
ten replicates, and feature-off/feature-on arms. Add a matched audit-on copy of
each worker, yielding 320 total fresh workers. Audit-on workers must preserve
the clean worker's semantic outcome and expose reconcilable counters. Clean
workers remain the only source of latency and memory performance estimates;
the audit-on copies are diagnostic and are never pooled into clean timing.

The runner will store each worker's training base and transfer base before
learning, serialize the complete graph after learning, reload it into a fresh
substrate with the same seed rules, and submit the held-out target through the
normal observation/closure path. Exact reuse is adjudicated by the substrate's
`DimInfer` result, generator receipt, zero unexplained transforms, and exact
registered oracle rows.

No confirmatory worker has run under the v2 lock. Any further changes to the
runner, analyzer, source, or fixtures after lock creation invalidate that lock
for confirmation and require a new amendment/version.
