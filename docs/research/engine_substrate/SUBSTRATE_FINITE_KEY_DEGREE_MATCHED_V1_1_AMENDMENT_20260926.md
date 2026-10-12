# Degree-matched closure v1.1 — injective-match oracle amendment

**Status: registered before v1.1 measurement.** The first harness launch stopped
at bidirected-star N=32, q=3: the native result had no Witness, and the runner
raised while assuming one existed. No complete raw matrix was emitted; retain
the original runner as the failed harness attempt.

## Source finding

`runners/dsl/src/rewrite.rs::extend_each` requires all bound match variables to
resolve to distinct nodes and skips a binding when two variables collide. The
v1 oracle counted arbitrary walks, including immediate returns such as
leaf→hub→leaf→hub in the star. Those are not valid native bindings.

## Correction

- Keep the graph families, sizes, edge counts, arities, repetitions, paired
  timing/audit arms, schedule, and metric definitions unchanged.
- Change the independent enumerator to enumerate injective node-simple paths,
  matching the explicit native all-different rule.
- Preserve the bidirected-star q=3 cell as a zero-match negative control. In that
  cell the exact terminal state contains no Witness and no result edges; all
  other cells must mint one fixed Witness and emit one result edge per distinct
  terminal binding node.
- Use versioned v1.1 runner/analyzer and preserve separate two-process captures.

## Admission and boundary

Require exact injective binding counts and terminal graph parity for positive
and zero-match cells, as well as fixed point, progress-bound, degree-histogram,
counter-conservation, and process-replication checks. This amendment narrows the
measured matcher semantics to the engine's actual injective binding contract;
it does not change the registered graph design or broaden the workload claim.
