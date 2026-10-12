# GenInfer pattern-structure factorial preregistration (2026-09-26)

## Question

At fixed 4 relations and fixed 6,560 candidate matrices, how do geometric point-set structure and predicate grouping affect GenInfer's ability to recover a known 2-D integer transform and its direct evaluation cost?

## Locked factorial

Use a 4×3 design: four asymmetric coordinate sets (`elbow`, `staircase`, `branch`, `long_arm`) crossed with three predicate grouping conditions (`shared`, `paired`, `unique`). Each cell has exactly four relations; coordinates use the same known matrix `[2,1,1,1]`. Every cell must yield data-derived bound B=4 and exactly 6,560 candidate matrices. Point sets are:

- elbow: `(0,0),(0,1),(1,0),(2,0)`
- staircase: `(0,0),(0,1),(1,1),(2,0)`
- branch: `(0,0),(1,0),(1,1),(2,0)`
- long_arm: `(0,0),(0,1),(1,0),(1,2)`

Predicate grouping uses one shared label for all four rows, two labels with two rows each, or four unique labels. Relation/predicate assignments are fixed in the runner and preserved in base and transformed goal. One fresh native substrate per cell is prepared before timing. One untimed warm-up is followed by five timed `GenInfer(field=matrix)` calls per cell; condition order is deterministically shuffled with a locked seed each repetition. `field=checked` is read outside the timed interval.

## Required gates and analysis

The analyzer independently verifies the 12 cells, exact input coordinates and predicate multiplicities, four base/goal relations, matrix output `[2,1,1,1]` on every timed call, B=4, 6,560 checked candidates per cell, finite positive timings, five samples per cell, fixed seed/order, and current native/source hashes. Report median/min/max times by cell and summarize geometry/predicate effects descriptively. There is no timing pass threshold and no assumed monotonic ordering.

## Claim boundary

This evaluates exact positive recovery and direct evaluator cost across 12 small, authored 2-D structures within one linear-transform class. It does not test noisy or negative cases, new transform families, automatic mint/closure cost, higher dimensions, larger search bounds, learned frame locality, or natural-task capability. The prior relation-count result remains the only evidence about relation-count scaling.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_pattern_structure_probe_v1.py
python3 scripts/analyze_substrate_geninfer_pattern_structure_probe_v1.py
```
