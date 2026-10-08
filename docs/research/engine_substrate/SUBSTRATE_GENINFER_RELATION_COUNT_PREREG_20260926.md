# GenInfer relation-count scaling preregistration

**Lock date:** 2026-09-26, before capture  
**Experiment type:** direct evaluator cost isolation within the supported 2-D family

## Question

At fixed data-derived matrix bound B=4 and fixed 6,560 enumerated candidates, how does the time per `GenInfer` call vary with the number of held/observed relations that each candidate transforms and matches?

## Fixture and schedule

- Each condition contains a four-cell asymmetric L signature repeated as distinct predicate-labeled copies. Relation counts are exactly 4, 8, 16, 32, and 64. Every copy has the same coordinates and value pattern; its predicate label is unique and unchanged by the transform.
- The fixed transform is `[2,1,1,1]`. It maps each copied L signature to the target and keeps the normalized maximum coordinate B=4 at every relation count.
- One fresh native substrate and one `ShapeSignature` node are constructed per relation-count condition. These are built before timing; five `GenInfer(field=matrix)` evaluations are timed per condition on that unchanged graph.
- One untimed 4-relation warm-up precedes the measured schedule. Measured repetitions run in ascending relation-count order, five rounds total.
- One separate, untimed `field=checked` evaluation verifies the fixed 6,560 candidate count for every condition.

## Locked checks and analysis

The runner must emit 25 timed calls, each with the exact expected matrix, and all five conditions must report exactly 6,560 candidates. The analyzer verifies counts, matrix outcomes, schedule, native artifact and source hashes. It reports median/min/max per-call time, candidate throughput, and the median-time ratio relative to four relations. There is no time threshold or required scaling exponent; any semantically valid timing curve is recorded without a performance pass/fail judgment.

## Claim boundary

This isolates relation-count cost in repeated, predicate-distinguished copies of one four-cell motif at one bound. It does not sample diverse shape structures, higher dimensions, larger B, noise, full seed closure, graph construction, memory, or natural-task distributions. Copy count can reveal matching/scanning cost for this motif but cannot stand in for arbitrary shape complexity.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_relation_count_probe_v1.py
python3 scripts/analyze_substrate_geninfer_relation_count_probe_v1.py
```
