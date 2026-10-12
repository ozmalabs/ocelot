# GenInfer transform-family recovery preregistration (2026-09-26)

## Question

Can the current GenInfer path recover several distinct invertible 2-D integer linear maps with the same four-relation input size and the same data-derived search bound, and how does direct-call cost vary across these transform families?

## Conditions

Four locked matrices, all row-major, all invertible, with different coefficient patterns:

| Family | Matrix |
|---|---|
| asymmetric scale-shear | `[1,1,0,2]` |
| anisotropic scale | `[2,0,0,1]` |
| swap-scale | `[0,2,1,0]` |
| coupled shear | `[2,0,1,1]` |

Every condition transforms the same four unique-predicate relations `p0:(0,0)`, `p1:(1,0)`, `p2:(2,0)`, `p3:(0,2)`. The signature and target are generated before timing. Each condition must derive search bound B=4 and exactly 6,560 candidate matrices. Unique predicate labels make each input-output correspondence explicit. Use one fresh native substrate per condition, one untimed warm-up, five timed direct `GenInfer(field=matrix)` calls per condition, and one untimed `field=checked` read. Shuffle condition order deterministically per repetition with a fixed seed.

## Gates and analysis

Independent analysis verifies all four matrices and source inputs, relation counts, invertibility, computed bound and candidate formula, exact output matrix on every call, sample count, schedule, finite timings, and current source/native hashes. Report per-family medians and ranges plus ratios to the first condition. No speed threshold or transform ranking is assumed.

## Claim boundary

This is positive direct-evaluator evidence across four matrices in one 2-D integer-linear class. It does not evaluate non-linear transforms, noise, noninvertible maps, higher dimensions, automatic minting/closure cost, or natural-task learning. It complements (and does not replace) the fixed-transform geometry/predicate factorial.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_transform_family_probe_v1.py
python3 scripts/analyze_substrate_geninfer_transform_family_probe_v1.py
```
